#!/usr/bin/env python3
"""运行隔离的真实客户端任务；客观检查通过后仍须独立审查。"""
import argparse
from datetime import date, timedelta
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

# Claude 默认要审批 Bash；开沙箱后自动放行，写入仍限于工作区，与 Codex workspace-write 对等。
CLAUDE_SANDBOX = json.dumps({'sandbox': {'enabled': True, 'autoAllowBashIfSandboxed': True}})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(workspace, *args):
    return subprocess.check_output(['git', '-C', str(workspace), *args], text=True, stderr=subprocess.STDOUT)


def command(client, workspace, response):
    if client == 'codex':
        # 不加 --ephemeral：它不写 rollout，spawn_agent 会以 no rollout found 失败。
        return ['codex', 'exec', '--sandbox', 'workspace-write', '--json',
                '-C', str(workspace), '-o', str(response), '-']
    return ['claude', '-p', '--output-format', 'stream-json', '--verbose',
            '--permission-mode', 'acceptEdits', '--settings', CLAUDE_SANDBOX]


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
    # 验收类场景的待验收改动留在工作区，不提交。
    for name, content in case.get('changes', {}).items():
        path = workspace/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
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
            message = event.get('message')
            blocks = message.get('content') if isinstance(message, dict) else None
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


COLLAB_TOOLS = {'spawn_agent', 'wait_agent', 'send_message', 'list_agents', 'interrupt_agent', 'close_agent'}


def child_ran_tools(records):
    """子线程开头是继承的父线程历史，只看 subagent_history_start_ordinal 之后的实际工具调用。"""
    meta = records[0].get('payload', {}) if records and records[0].get('type') == 'session_meta' else {}
    start = int(meta.get('subagent_history_start_ordinal') or 0)
    called, answered = set(), set()
    for record in records[start:]:
        payload = record.get('payload') if isinstance(record, dict) else None
        if record.get('type') != 'response_item' or not isinstance(payload, dict):
            continue
        if payload.get('type') in ('function_call', 'custom_tool_call') and payload.get('name') not in COLLAB_TOOLS:
            called.add(payload.get('call_id'))
        elif payload.get('type') in ('function_call_output', 'custom_tool_call_output'):
            answered.add(payload.get('call_id'))
    return bool(called & answered)


def rollout_reviewers(records, children):
    """Codex 新版只在 rollout 里记录派发与 FINAL_ANSWER；子线程须有自己实际执行的工具调用。"""
    calls, spawned, completed = set(), set(), set()
    for record in records:
        payload = record.get('payload') if isinstance(record, dict) else None
        if record.get('type') != 'response_item' or not isinstance(payload, dict):
            continue
        if payload.get('type') == 'function_call' and payload.get('name') == 'spawn_agent' and payload.get('call_id'):
            calls.add(payload['call_id'])
        elif payload.get('type') == 'function_call_output' and payload.get('call_id') in calls:
            try:
                name = json.loads(payload.get('output') or '').get('task_name')
            except (json.JSONDecodeError, AttributeError):
                name = None
            if name:
                spawned.add(name)
        elif payload.get('type') == 'agent_message' and payload.get('author') in spawned:
            text = ''.join(block.get('text', '') for block in payload.get('content') or [] if isinstance(block, dict))
            answer = text.split('Payload:', 1)[1].strip() if 'Payload:' in text else ''
            if 'FINAL_ANSWER' in text and answer and child_ran_tools(children.get(payload['author'], [])):
                completed.add(payload['author'])
    return completed


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def find_rollouts(events):
    """按 thread.started 的 id 找 Codex 父 rollout 和 parent_thread_id 指向它的子 rollout；找不到时不推断成功。"""
    thread = next((e.get('thread_id') for e in events if e.get('type') == 'thread.started' and e.get('thread_id')), None)
    if not thread:
        return None, {}
    sessions = Path(os.environ.get('CODEX_HOME', Path.home()/'.codex'))/'sessions'
    parent = next(iter(sorted(sessions.glob(f'*/*/*/rollout-*-{thread}.jsonl'))), None)
    children = {}
    if parent:
        # 会话目录按日期分，子 agent 可能跨过午夜落进下一天的目录。
        day = date(*map(int, parent.parent.relative_to(sessions).parts))
        following = sessions/(day + timedelta(days=1)).strftime('%Y/%m/%d')
        for path in sorted([*parent.parent.glob('rollout-*.jsonl'), *following.glob('rollout-*.jsonl')]):
            with path.open() as handle:
                first = handle.readline()
            try:
                meta = json.loads(first).get('payload', {})
            except json.JSONDecodeError:
                continue
            if meta.get('parent_thread_id') == thread and meta.get('agent_path'):
                children[meta['agent_path']] = path
    return parent, children


def event_summary(path, client, rollout=None, children=None):
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
        tools=0
        for e in events:
            message=e.get('message')
            blocks=message.get('content') if isinstance(message,dict) else None
            if isinstance(blocks,list):
                tools+=sum(isinstance(block,dict) and block.get('type')=='tool_use' for block in blocks)
        usage=terminal[-1].get('usage')
    reviewers = set(independent_reviewers(events,client))
    if rollout is not None:
        reviewers |= rollout_reviewers(read_jsonl(rollout), {name: read_jsonl(child) for name, child in (children or {}).items()})
    return {'events':len(events),'tool_events':tools,'usage':usage, 'independent_reviewers':sorted(reviewers)}


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


def forget_trust(workspace):
    """Codex 会把临时工作区记成 trusted 项目；只删这一个工作区的那一段，其余配置原样保留。"""
    config = Path(os.environ.get('CODEX_HOME', Path.home()/'.codex'))/'config.toml'
    if not config.is_file():
        return False
    headers = {f'[projects."{path}"]' for path in (str(workspace), str(Path(workspace).resolve()))}
    kept, skipping, changed = [], False, False
    for line in config.read_text().splitlines(keepends=True):
        if line.startswith('['):
            skipping = line.strip() in headers
            changed |= skipping
        if not skipping:
            kept.append(line)
    if changed:
        config.write_text(''.join(kept))
    return changed


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
        rollout, children = None, {}
        if client == 'codex':
            found, found_children = find_rollouts(read_jsonl(events))
            if found:
                rollout = destination/'rollout.jsonl'
                shutil.copyfile(found, rollout)
            for index, (name, path) in enumerate(sorted(found_children.items())):
                children[name] = destination/f'rollout-child-{index+1}.jsonl'
                shutil.copyfile(path, children[name])
        result['events'] = event_summary(events,client,rollout,children)
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
        if client == 'codex':
            try:
                result['trust_entry_removed'] = forget_trust(workspace)
            except OSError:
                result['trust_entry_removed'] = False
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
