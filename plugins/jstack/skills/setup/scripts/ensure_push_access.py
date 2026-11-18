#!/usr/bin/env python3
"""确保当前活跃 gh 账号对目标仓库有写权限（ADMIN/MAINTAIN/WRITE），必要时自动切换已登录账号。
用法：python3 ensure_push_access.py [项目目录]
"""
import re
import sys
from pathlib import Path

import check_env

PUSH_WRITABLE = {"ADMIN", "MAINTAIN", "WRITE"}


def resolve_repo(root: Path):
    code, remotes = check_env.run("git", "remote", "-v", cwd=root)
    if code != 0:
        return None, "git_remote_failed"
    repos = check_env.github_repos(remotes)
    if not repos:
        return None, "no_github_remote"
    if len(repos) == 1:
        return repos[0], None
    code, view = check_env.run("gh", "repo", "set-default", "--view", cwd=root)
    repo = view.strip()
    if code == 0 and repo in repos:
        return repo, None
    return None, "default_repo_unset"


def parse_accounts(status_text: str):
    """从 `gh auth status` 输出解析 (已登录账号列表, 当前活跃账号)。"""
    accounts, active = [], None
    current = None
    for line in status_text.splitlines():
        m = re.search(r"Logged in to github\.com account (\S+)", line)
        if m:
            current = m.group(1)
            if current not in accounts:
                accounts.append(current)
            continue
        if current and re.search(r"Active account:\s*true", line, re.I):
            active = current
    return accounts, active


def viewer_permission(repo: str):
    code, perm = check_env.run("gh", "repo", "view", repo, "--json", "viewerPermission", "--jq", ".viewerPermission")
    return perm.strip() if code == 0 else ""


def ensure_access(root: Path) -> int:
    repo, err = resolve_repo(root)
    if err:
        print(f"push_access=error reason={err}")
        return 1

    perm = viewer_permission(repo)
    if perm in PUSH_WRITABLE:
        print(f"repo={repo}")
        print("push_access=ok")
        return 0

    code, status_out = check_env.run("gh", "auth", "status")
    if code != 0:
        print(f"repo={repo}")
        print(f"push_access=error reason=gh_auth_status_failed detail={status_out.strip()}")
        return 1

    accounts, original = parse_accounts(status_out)
    for acc in accounts:
        if acc == original:
            continue
        sw_code, _ = check_env.run("gh", "auth", "switch", "-u", acc)
        if sw_code != 0:
            continue
        if viewer_permission(repo) in PUSH_WRITABLE:
            print(f"repo={repo}")
            print(f"switched={acc}")
            print("push_access=ok")
            return 0

    if original:
        check_env.run("gh", "auth", "switch", "-u", original)
    print(f"repo={repo}")
    print(f"push_access=denied repo={repo}")
    return 1


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    return ensure_access(root)


if __name__ == "__main__":
    sys.exit(main())
