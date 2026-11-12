#!/usr/bin/env python3
"""只读检查 jstack 的运行环境，不修改任何东西。用法：python3 check_env.py [项目目录]。
每行输出 `<检查项>=<结果>`；任一必需项不满足时退出码为 1。"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 挂子 issue、设阻塞关系、指派和关闭 issue 至少需要 TRIAGE
WRITABLE = {"ADMIN", "MAINTAIN", "WRITE", "TRIAGE"}


def run(*cmd, cwd=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return p.returncode, p.stdout + p.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def github_repos(remote_text):
    """从 `git remote -v` 输出里取出所有不重复的 GitHub owner/repo，保持出现顺序。"""
    found = re.findall(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?(?:\s|$)", remote_text)
    return list(dict.fromkeys(f"{o}/{r}" for o, r in found))


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    out, missing = {}, []
    out["git"] = "ok" if shutil.which("git") else "missing"
    out["gh"] = "ok" if shutil.which("gh") else "missing"
    repo = ""
    if out["gh"] == "ok":
        code, _ = run("gh", "auth", "status")
        out["gh_auth"] = "ok" if code == 0 else "not_logged_in"
        _, help_text = run("gh", "issue", "create", "--help")
        lacking = [f for f in ("--blocked-by", "--parent") if f not in help_text]
        out["gh_features"] = "ok" if not lacking else "missing " + ",".join(lacking)
    if out["git"] == "ok":
        _, remotes = run("git", "remote", "-v", cwd=root)
        repos = github_repos(remotes)
        out["github_remote"] = ",".join(repos) or "none"
        if len(repos) == 1:
            repo = repos[0]
        elif len(repos) > 1 and out.get("gh") == "ok":
            # 多个 GitHub remote 时，gh 需要用 `gh repo set-default` 指定默认仓库
            code, view = run("gh", "repo", "set-default", "--view", cwd=root)
            repo = view.strip() if code == 0 and view.strip() in repos else ""
            out["default_repo"] = repo or "unset"
    if repo and out.get("gh_auth") == "ok":
        code, perm = run("gh", "repo", "view", repo, "--json", "viewerPermission", "--jq", ".viewerPermission")
        perm = perm.strip() if code == 0 else "unknown"
        out["gh_permission"] = "ok" if perm in WRITABLE else "insufficient " + perm
    for k, v in out.items():
        print(f"{k}={v}")
    required = {"git": "ok", "gh": "ok", "gh_auth": "ok", "gh_features": "ok"}
    missing = [k for k, v in required.items() if out.get(k) != v]
    if out.get("gh_permission", "ok") != "ok":
        missing.append("gh_permission")
    if out.get("github_remote", "none") == "none":
        missing.append("github_remote")
    if out.get("default_repo") == "unset":
        missing.append("default_repo")
    print("result=" + ("ok" if not missing else "blocked " + ",".join(missing)))
    return 1 if missing else 0


if __name__ == "__main__":
    assert github_repos("origin\thttps://github.com/a-b/c.d.git (fetch)\norigin\thttps://github.com/a-b/c.d.git (push)") == ["a-b/c.d"]
    assert github_repos("origin\tgit@github.com:a/b (push)\nup\thttps://github.com/x/b.git (fetch)") == ["a/b", "x/b"]
    assert github_repos("origin\thttps://gitlab.com/a/b.git (fetch)") == []
    sys.exit(main())
