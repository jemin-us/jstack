#!/usr/bin/env python3
"""运行隔离的真实客户端任务；客观检查通过后仍须独立审查。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from cases import CASES


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(workspace, *args):
    return subprocess.check_output(['git', '-C', str(workspace), *args], text=True, stderr=subprocess.STDOUT)


def command(client, workspace, response):
    if client == 'codex':
        return ['codex', 'exec', '--ephemeral', '--sandbox', 'workspace-write', '--json',
                '-C', str(workspace), '-o', str(response), '-']
    return ['claude', '-p', '--output-format', 'stream-json', '--verbose',
            '--permission-mode', 'acceptEdits']


def execute(argv, cwd, stdout_path, stderr_path, timeout, prompt=None):
    """超时终止进程组，保留日志；不通过 shell 拼接用户内容。"""
    started = time.monotonic()
    with stdout_path.open('w') as out, stderr_path.open('w') as err:
        process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE if prompt is not None else subprocess.DEVNULL,
                                   stdout=out, stderr=err, text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
            return {'exit_code': process.returncode, 'elapsed_seconds': round(time.monotonic()-started, 3), 'timed_out': False}
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
            return {'exit_code': process.returncode, 'elapsed_seconds': round(time.monotonic()-started, 3), 'timed_out': True}


def prepare(case, source, root):
    workspace = root / 'project'
    workspace.mkdir()
    for name, content in case['files'].items():
        path = workspace/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    instructions = ('本仓库为本地开发项目。仅在当前工作区工作，不提交、不创建分支或PR、不访问真实业务数据。'
                    '不得读取工作区外的任务记录或判据。保留原始检查，不放宽断言。\n')
    if source:
        target = workspace/'.agents/skills'
        shutil.copytree(source/'skills', target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'evaluate'))
        (workspace/'.claude').mkdir()
        (workspace/'.claude/skills').symlink_to('../.agents/skills', target_is_directory=True)
        instructions += '开发任务先读 .agents/skills/mode/SKILL.md 并按适用流程执行；仅分析时保持只读。本地范围优先于技能的提交交付步骤。\n'
    (workspace/'AGENTS.md').write_text(instructions)
    (workspace/'CLAUDE.md').write_text(instructions)
    git(workspace, 'init', '-q')
    (workspace/'.git/info/exclude').write_text('.agents/\n.claude/\n__pycache__/\n*.pyc\n')
    git(workspace, 'add', '.')
    git(workspace, '-c', 'user.name=Local Runner', '-c', 'user.email=runner@example.invalid', 'commit', '-qm', 'Initial project')
    return workspace


def objective(case, workspace, before):
    """检查真实产物和只读边界，不解析候选的成功声明。"""
    failures = []
    if git(workspace, 'rev-parse', 'HEAD').strip() != before['head']:
        failures.append('禁止提交的任务产生了新提交')
    if git(workspace, 'branch', '--show-current').strip() != before['branch']:
        failures.append('任务切换了分支')
    if case.get('unchanged') and git(workspace, 'status', '--porcelain').strip():
        failures.append('只读任务修改了工作区')
    for name in case.get('protected', []):
        if not (workspace/name).is_file() or digest(workspace/name) != before['protected'][name]:
            failures.append(f'受保护文件被修改：{name}')
    return failures


def independent_reviewers(events, client):
    """提取可核实的独立执行完成记录；具体是否执行验收仍由非作者审查。"""
    completed = set()
    if client == 'codex':
        spawned = set()
        for event in events:
            item = event.get('item', {})
            if item.get('type') != 'collab_tool_call' or item.get('status') != 'completed':
                continue
            if item.get('tool') == 'spawn_agent':
                spawned.update(identity for identity in item.get('receiver_thread_ids', []) if identity)
            for identity, state in item.get('agents_states', {}).items():
                if identity in spawned and isinstance(state, dict) and state.get('status') == 'completed' and state.get('message'):
                    completed.add(identity)
    else:
        calls = set()
        for event in events:
            blocks = event.get('message', {}).get('content', [])
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get('type') == 'tool_use' and block.get('id') and block.get('name') in ('Agent', 'Task') and not block.get('input', {}).get('run_in_background'):
                    calls.add(block.get('id'))
                if block.get('type') == 'tool_result' and block.get('tool_use_id') in calls and not block.get('is_error') and block.get('content'):
                    completed.add(block['tool_use_id'])
    return sorted(completed)


def event_summary(path, client):
    """只接受客户端完整事件流；统计只用于证据索引，不判定任务成功。"""
    events=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not events or any(not isinstance(event,dict) for event in events):
        raise ValueError('缺少结构化事件')
    if client=='codex':
        terminal=[e for e in events if e.get('type') in ('turn.completed','turn.failed')]
        if not terminal or terminal[-1]['type']!='turn.completed':
            raise ValueError('没有成功结束的客户端轮次')
        tools=sum(e.get('type')=='item.completed' and e.get('item',{}).get('type') in ('command_execution','mcp_tool_call','file_change') for e in events)
        usage=terminal[-1].get('usage')
    else:
        terminal=[e for e in events if e.get('type')=='result']
        if not terminal or terminal[-1].get('is_error') or terminal[-1].get('subtype')!='success':
            raise ValueError('Claude 未成功结束')
        tools=sum(block.get('type')=='tool_use' for e in events for block in e.get('message',{}).get('content',[]) if isinstance(block,dict))
        usage=terminal[-1].get('usage')
    return {'events':len(events),'tool_events':tools,'usage':usage, 'independent_reviewers':independent_reviewers(events,client)}


def source_digest(workspace):
    """记录候选真正加载的源码，避免运行中源码变化后混淆变体。"""
    digest_value=hashlib.sha256()
    for path in sorted((workspace/'.agents/skills').rglob('*')):
        if path.is_file():
            digest_value.update(str(path.relative_to(workspace)).encode())
            digest_value.update(path.read_bytes())
    return digest_value.hexdigest()


def preserve_files(workspace, destination):
    """保存未跟踪产物和当前源码；不解引用候选创建的符号链接。"""
    names=git(workspace,'ls-files','-z').split('\0') + git(workspace,'ls-files','--others','--exclude-standard','-z').split('\0')
    for name in set(names)-{''}:
        path=workspace/name
        target=destination/'artifacts'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if path.is_symlink():
            target.with_name(target.name+'.symlink.txt').write_text(os.readlink(path))
        elif path.is_file() and not any(workspace.joinpath(*Path(name).parts[:index]).is_symlink() for index in range(1,len(Path(name).parts))):
            shutil.copyfile(path,target)


def run_case(case_name, client, source, destination, timeout):
    case = CASES[case_name]
    destination.mkdir(parents=True, exist_ok=False)
    # 候选看不到结果目录名和场景编号，默认路径仅使用随机项目名。
    root = Path(tempfile.mkdtemp(prefix='workspace-'))
    workspace = prepare(case, source, root)
    before = {'head': git(workspace,'rev-parse','HEAD').strip(), 'branch': git(workspace,'branch','--show-current').strip(),
              'protected': {name:digest(workspace/name) for name in case.get('protected',[])}}
    prompt = case['prompt'] + '\n完成后说明实际改动、运行的检查和未验证部分。'
    (destination/'prompt.txt').write_text(prompt)
    result = {'case':case_name, 'client':client, 'workspace':str(workspace),
              'source':str(source) if source else None, 'source_digest':source_digest(workspace), 'scope':'project-source-loading; inherited client configuration remains',
              'status':'BLOCKED', 'reason':'尚未执行', 'checks':[], 'review_criteria':case['review'], 'before':before}
    try:
        binary = shutil.which(client)
        if not binary:
            result['reason'] = '客户端命令不可用'
            return result
        version = subprocess.run([binary,'--version'],capture_output=True,text=True,timeout=15)
        result['client_version'] = version.stdout.strip()
        events = destination/'events.jsonl'
        response = workspace/'.response.txt'
        # response 由外层生成，避免被当作候选擅自修改只读仓库。
        with (workspace/'.git/info/exclude').open('a') as exclude:
            exclude.write('.response.txt\n')
        argv = command(client, workspace, response)
        result['invocation'] = argv
        process = execute(argv,workspace,events,destination/'stderr.txt',timeout,prompt)
        result['process'] = process
        if response.exists():
            shutil.copyfile(response,destination/'response.txt')
        elif client == 'claude':
            # 保留原始 stream-json；最终回复只是人类审查材料，不能用于自动判定。
            for line in events.read_text().splitlines():
                try:
                    event=json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get('type')=='result':
                    (destination/'response.txt').write_text(str(event.get('result','')))
        if process['timed_out'] or process['exit_code'] != 0:
            result['reason'] = '客户端超时' if process['timed_out'] else '客户端执行失败，检查事件与错误日志'
            return result
        if not events.stat().st_size or not (destination/'response.txt').is_file():
            result['reason'] = '缺少事件或最终回复证据'
            return result
        result['events'] = event_summary(events,client)
        failures = objective(case,workspace,before)
        for index, argv in enumerate(case['checks']):
            state = execute(argv, workspace, destination/f'check-{index}.stdout', destination/f'check-{index}.stderr', 30)
            state['command'] = argv
            result['checks'].append(state)
            if state['timed_out']:
                result['reason'] = '外部判据超时'
                return result
            if state['exit_code'] != 0:
                failures.append(f'外部检查 {index} 失败')
        if failures:
            result['status'], result['reason'] = 'FAIL', '; '.join(failures)
        elif not case.get('unchanged') and not result['events']['independent_reviewers']:
            result['status'], result['reason'] = 'BLOCKED', '产物检查通过，但缺少可核实的独立执行完成记录；候选自述不能补足'
        else:
            result['status'], result['reason'] = 'NEEDS_REVIEW', '客观检查通过，仍须独立核对真实工具记录、子任务范围和语义判据'
        return result
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result['reason'] = f'运行基础设施错误：{type(exc).__name__}'
        return result
    finally:
        try:
            (destination/'diff.patch').write_text(git(workspace,'diff',before['head']))
            (destination/'git-status.txt').write_text(git(workspace,'status','--short'))
            result['head'] = git(workspace,'rev-parse','HEAD').strip()
            preserve_files(workspace,destination)
        except (OSError, subprocess.SubprocessError):
            result['reason'] += '; Git 状态无法获取'
            result['status'] = 'BLOCKED'
        (destination/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--client',choices=['codex','claude'])
    parser.add_argument('--case',choices=['all',*CASES],default='all')
    parser.add_argument('--source',type=Path,help='jstack 源码根目录；省略则不注入项目技能，但客户端全局配置仍可能生效')
    parser.add_argument('--out',type=Path)
    parser.add_argument('--repeat',type=int,default=1)
    parser.add_argument('--timeout',type=int,default=600)
    args=parser.parse_args()
    if args.list:
        print('\n'.join(CASES)); return 0
    if not args.client or not args.out or args.repeat < 1 or args.timeout < 1:
        parser.error('需要 --client、--out 及正数 repeat/timeout')
    if args.source and not (args.source/'skills/mode/SKILL.md').is_file():
        parser.error('--source 必须是包含 skills/mode/SKILL.md 的 jstack 源码根目录')
    source=args.source.resolve() if args.source else None
    output=args.out.resolve()
    selected=list(CASES) if args.case=='all' else [args.case]
    summaries=[]
    for case_name in selected:
        for iteration in range(args.repeat):
            destination=output/f'{case_name}-{iteration+1}'
            if destination.exists():
                parser.error(f'结果目录已存在，不覆盖：{destination}')
            result=run_case(case_name,args.client,source,destination,args.timeout)
            summaries.append(result)
            print(json.dumps({'case':case_name,'run':iteration+1,'status':result['status'],'reason':result['reason']},ensure_ascii=False),flush=True)
    # NEEDS_REVIEW 不是通过；退出码 0 只表示候选执行与客观检查完成。
    return 0 if all(x['status']=='NEEDS_REVIEW' for x in summaries) else 1


if __name__=='__main__':
    sys.exit(main())
