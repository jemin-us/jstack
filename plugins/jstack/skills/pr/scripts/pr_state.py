#!/usr/bin/env python3
"""读取单个 GitHub PR 的交付状态；只读，不回复 review，不 push，不合并。"""
import argparse
import json
import subprocess
import sys


def classify(pr, threads, verified_head):
    """按当前 HEAD 和完整检查证据判定，未知状态不放行。"""
    head = pr.get('headRefOid')
    def result(state, reason):
        return {'state': state, 'reason': reason, 'head': head, 'url': pr.get('url')}
    if pr.get('state') in ('MERGED', 'CLOSED'):
        return result(pr['state'], 'PR 已结束，不再执行开发操作')
    if pr.get('state') != 'OPEN' or not head:
        return result('BLOCKED', '缺少 PR 状态或 HEAD')
    if pr.get('isDraft'):
        return result('BLOCKED', 'PR 仍为 draft')
    if pr.get('mergeable') == 'CONFLICTING':
        return result('BLOCKED', '基准分支冲突，须由分支拥有者处理并重新验证')
    if threads is None:
        return result('BLOCKED', 'review threads 未完整读取')
    if any(not t.get('isResolved', False) for t in threads):
        return result('REVIEW_REQUIRED', '有未解决的 review thread，须核实内容后处理')
    if pr.get('reviewDecision') == 'CHANGES_REQUESTED':
        return result('REVIEW_REQUIRED', 'review 要求修改')
    if pr.get('reviewDecision') not in (None, '', 'APPROVED', 'REVIEW_REQUIRED'):
        return result('BLOCKED', '未知 review 状态')
    checks = pr.get('statusCheckRollup')
    if not checks:
        return result('BLOCKED', '没有检查证据，不能宣称 CI 通过')
    pending = False
    for check in checks:
        if check.get('__typename') == 'CheckRun':
            if check.get('status') in ('QUEUED', 'IN_PROGRESS', 'WAITING', 'REQUESTED', 'PENDING'):
                pending = True
                continue
            if check.get('status') != 'COMPLETED':
                return result('BLOCKED', '未知 check 状态')
            conclusion = check.get('conclusion')
            if conclusion in ('FAILURE', 'TIMED_OUT', 'CANCELLED', 'ACTION_REQUIRED', 'STARTUP_FAILURE', 'STALE'):
                return result('FAILED', 'CI 检查失败或失效')
            if conclusion != 'SUCCESS':
                return result('BLOCKED', '检查跳过、中性或缺少成功结论')
        elif check.get('__typename') == 'StatusContext':
            if check.get('state') in ('PENDING', 'EXPECTED'):
                pending = True
            elif check.get('state') in ('ERROR', 'FAILURE'):
                return result('FAILED', '提交状态检查失败')
            elif check.get('state') != 'SUCCESS':
                return result('BLOCKED', '未知提交状态')
        else:
            return result('BLOCKED', '未知检查类型')
    if pending:
        return result('WAITING', '当前 HEAD 的检查仍在运行')
    if pr.get('reviewDecision') == 'REVIEW_REQUIRED':
        return result('WAITING', '等待仓库要求的批准')
    if pr.get('mergeable') != 'MERGEABLE' or pr.get('mergeStateStatus') != 'CLEAN':
        return result('BLOCKED', 'GitHub 尚未报告 CLEAN/MERGEABLE')
    if verified_head != head:
        return result('VERIFICATION_REQUIRED', '独立验收未覆盖当前 HEAD')
    return result('READY', '当前 HEAD 的检查、review 和独立验收条件均满足')


def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], text=True, timeout=30))


def fetch(pr_number):
    fields = 'number,state,isDraft,baseRefName,headRefOid,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,url'
    pr = gh('pr', 'view', str(pr_number), '--json', fields)
    repo = gh('repo', 'view', '--json', 'name,owner')
    query = '''query($owner:String!,$name:String!,$number:Int!,$cursor:String){
      repository(owner:$owner,name:$name){pullRequest(number:$number){
        headRefOid reviewThreads(first:100,after:$cursor){
          nodes{isResolved isOutdated} pageInfo{hasNextPage endCursor}
        }
      }}
    }'''
    threads, cursor = [], None
    while True:
        args = ['api', 'graphql', '-f', f'query={query}', '-f', f'owner={repo["owner"]["login"]}',
                '-f', f'name={repo["name"]}', '-F', f'number={pr["number"]}']
        if cursor:
            args += ['-f', f'cursor={cursor}']
        data = gh(*args)
        if data.get('errors'):
            raise ValueError('GraphQL 返回错误，review threads 未完整读取')
        node = data['data']['repository']['pullRequest']
        if node['headRefOid'] != pr['headRefOid']:
            raise ValueError('读取期间 PR HEAD 已变化，请重新获取状态')
        page = node['reviewThreads']
        threads.extend(page['nodes'])
        if not page['pageInfo']['hasNextPage']:
            break
        next_cursor = page['pageInfo']['endCursor']
        if not next_cursor or next_cursor == cursor:
            raise ValueError('review thread 分页未前进')
        cursor = next_cursor
    return pr, threads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pr', required=True, type=int)
    parser.add_argument('--verified-head', help='独立验收记录实际覆盖的完整 SHA，不可填未经验证的当前值')
    args = parser.parse_args()
    try:
        pr, threads = fetch(args.pr)
        result = classify(pr, threads, args.verified_head)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result = {'state': 'BLOCKED', 'reason': f'无法完整读取 PR：{type(exc).__name__}'}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['state'] in ('READY', 'MERGED', 'CLOSED') else 1


if __name__ == '__main__':
    sys.exit(main())
