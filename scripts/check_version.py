#!/usr/bin/env python3
"""检查发布规则：改了 skills/ 或 .claude-plugin/ 时，插件版本必须递增。

用法：python3 scripts/check_version.py <base> <head>。比较 git diff <base>...<head>，
两个版本号都从对应 commit 的 .claude-plugin/plugin.json 读取。不符合时输出原因，退出码为 1。
"""
import json
import re
import subprocess
import sys

WATCHED = ("skills/", ".claude-plugin/")
MANIFEST = ".claude-plugin/plugin.json"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def version_at(ref):
    """返回 ref 上 plugin.json 的版本号元组；ref 上没有 plugin.json 时返回 None。"""
    try:
        text = git("show", f"{ref}:{MANIFEST}")
    except subprocess.CalledProcessError:
        return None
    raw = str(json.loads(text).get("version", ""))
    m = VERSION_RE.match(raw)
    if not m:
        raise ValueError(f"{ref} 上 {MANIFEST} 的 version '{raw}' 不是 x.y.z 格式")
    return tuple(int(x) for x in m.groups())


def main():
    if len(sys.argv) != 3:
        print("用法：python3 scripts/check_version.py <base> <head>")
        return 1
    base, head = sys.argv[1:]
    try:
        changed = [p for p in git("diff", "--name-only", f"{base}...{head}").splitlines() if p.startswith(WATCHED)]
        if not changed:
            print("通过：没有改动 skills/ 或 .claude-plugin/，不要求递增版本")
            return 0
        old, new = version_at(base), version_at(head)
    except subprocess.CalledProcessError as e:
        print(f"✗ git 命令失败：{' '.join(e.cmd)}\n{e.stderr.strip()}")
        return 1
    except ValueError as e:
        print(f"✗ {e}")
        return 1
    if new is None:
        print(f"✗ {head} 上没有 {MANIFEST}")
        return 1
    fmt = lambda v: ".".join(map(str, v))
    if old is not None and new <= old:
        print(f"✗ 改动了 {len(changed)} 个 skills/ 或 .claude-plugin/ 下的文件（例如 {changed[0]}），"
              f"但 {MANIFEST} 的 version 没有递增：{base} 为 {fmt(old)}，{head} 为 {fmt(new)}")
        return 1
    print(f"通过：version 从 {fmt(old) if old else '无'} 升到 {fmt(new)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
