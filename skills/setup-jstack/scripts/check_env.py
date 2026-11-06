#!/usr/bin/env python3
"""只读检查 jstack 的运行环境，不修改任何东西。用法：python3 check_env.py [项目目录]。
每行输出 `<检查项>=<结果>`；任一必需项不满足时退出码为 1。"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

LABELS = ("jstack:spec", "jstack:ticket")
# 建标签、挂子 issue、设阻塞关系至少需要 TRIAGE
WRITABLE = {"ADMIN", "MAINTAIN", "WRITE", "TRIAGE"}


def run(*cmd, cwd=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return p.returncode, p.stdout + p.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def github_repo(remote_text):
    """从 `git remote -v` 输出里取第一个 GitHub 的 owner/repo。"""
    m = re.search(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?(?:\s|$)", remote_text)
    return f"{m.group(1)}/{m.group(2)}" if m else ""


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
        repo = github_repo(remotes)
        out["github_remote"] = repo or "none"
    if repo and out.get("gh_auth") == "ok":
        code, labels = run("gh", "label", "list", "--repo", repo, "--limit", "200", "--json", "name", "--jq", ".[].name")
        have = set(labels.split()) if code == 0 else set()
        lack = [l for l in LABELS if l not in have]
        out["labels"] = "ok" if code == 0 and not lack else ("missing " + ",".join(lack) if code == 0 else "unknown")
        code, perm = run("gh", "repo", "view", repo, "--json", "viewerPermission", "--jq", ".viewerPermission")
        perm = perm.strip() if code == 0 else "unknown"
        out["gh_permission"] = "ok" if perm in WRITABLE else "insufficient " + perm
    agents = root / "AGENTS.md"
    out["agents_md"] = ("has_jstack_block" if re.search(r"^## jstack\s*$", agents.read_text(encoding="utf-8"), re.M)
                        else "no_jstack_block") if agents.is_file() else "absent"
    claude = root / "CLAUDE.md"
    if claude.is_file():
        out["claude_md"] = "imports_agents" if "@AGENTS.md" in claude.read_text(encoding="utf-8") else "missing_import"
    else:
        out["claude_md"] = "absent"
    for k, v in out.items():
        print(f"{k}={v}")
    required = {"git": "ok", "gh": "ok", "gh_auth": "ok", "gh_features": "ok"}
    missing = [k for k, v in required.items() if out.get(k) != v]
    if out.get("gh_permission", "ok") != "ok":
        missing.append("gh_permission")
    if out.get("github_remote", "none") == "none":
        missing.append("github_remote")
    print("result=" + ("ok" if not missing else "blocked " + ",".join(missing)))
    return 1 if missing else 0


if __name__ == "__main__":
    assert github_repo("origin\thttps://github.com/a-b/c.d.git (fetch)") == "a-b/c.d"
    assert github_repo("origin\tgit@github.com:a/b (push)") == "a/b"
    assert github_repo("origin\thttps://gitlab.com/a/b.git (fetch)") == ""
    sys.exit(main())
