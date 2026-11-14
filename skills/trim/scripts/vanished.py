#!/usr/bin/env python3
"""列出精简后消失或被改掉的每一行，供逐行对照确认过的清单。只读。

用法：
  python3 vanished.py --git <起点 commit> [-- <路径> ...]   仓库内文件
  python3 vanished.py --pair <改前副本> <改后文件> [...]     仓库外文件（先备份改前副本）
"""
import argparse
import difflib
from pathlib import Path
import subprocess


def git_lines(base, paths):
    out = subprocess.run(["git", "diff", "-U0", base, "--", *paths], capture_output=True, text=True, check=True).stdout
    result, current = [], None
    for line in out.splitlines():
        if line.startswith("--- "):
            current = line[6:] if line.startswith("--- a/") else line[4:]
        elif line.startswith("-") and not line.startswith("---") and line[1:].strip():
            result.append((current, line[1:]))
    return result


def pair_lines(before, after):
    a = Path(before).read_text(encoding="utf-8").splitlines()
    b = Path(after).read_text(encoding="utf-8").splitlines() if Path(after).exists() else []
    return [(str(after), l[1:]) for l in difflib.unified_diff(a, b, lineterm="", n=0)
            if l.startswith("-") and not l.startswith("---") and l[1:].strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--git")
    ap.add_argument("--pair", nargs=2, action="append", default=[])
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args(argv)
    lines = (git_lines(a.git, a.paths) if a.git else []) + [x for p in a.pair for x in pair_lines(*p)]
    current = None
    for f, text in lines:
        if f != current:
            print(f"\n## {f}")
            current = f
        print(f"- {text}")
    print(f"\n共 {len(lines)} 行。")


if __name__ == "__main__":
    main()
