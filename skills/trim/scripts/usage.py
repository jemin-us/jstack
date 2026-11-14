#!/usr/bin/env python3
"""从两端的会话记录统计每个 skill 的真实调用。只读。

只认工具调用：Claude Code 的 Skill 工具和读取 SKILL.md 的工具调用，Codex 读取 SKILL.md 的
function_call。Codex 会把所有 skill 的路径注入每个会话，按名字 grep 全文会让每个 skill 都像被用过。
读取按路径分两类：路径里有 /plugins/ 的算已安装插件的使用，其余多半是在源码仓库里开发 skill。

用法：python3 usage.py <skill 名> [...]
"""
import argparse
from collections import Counter
import json
from pathlib import Path


def hits(names, text):
    """返回 (已安装插件读取, 源码读取) 两个集合。"""
    inst, src = set(), set()
    for n in names:
        key = f"/{n}/SKILL.md"
        i = text.find(key)
        while i >= 0:
            (inst if "/plugins/" in text[max(0, i - 200):i] else src).add(n)
            i = text.find(key, i + 1)
    return inst, src


def claude_counts(names, root):
    calls, reads, dev = Counter(), Counter(), Counter()
    for f in root.glob("**/*.jsonl"):
        seen, seen_dev = set(), set()
        for line in open(f, errors="ignore"):
            if '"tool_use"' not in line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            msg = e.get("message")
            blocks = msg.get("content") if isinstance(msg, dict) else None
            for b in blocks if isinstance(blocks, list) else []:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                inp = b.get("input") or {}
                skill = str(inp.get("skill", "")).split(":")[-1]
                if b.get("name") == "Skill" and skill in names:
                    calls[skill] += 1
                inst, src = hits(names, json.dumps(inp, ensure_ascii=False))
                seen |= inst
                seen_dev |= src
        reads.update(seen)
        dev.update(seen_dev)
    return calls, reads, dev


def codex_counts(names, roots):
    reads, dev = Counter(), Counter()
    for root in roots:
        for f in root.glob("**/*.jsonl"):
            seen, seen_dev = set(), set()
            for line in open(f, errors="ignore"):
                if '"function_call"' in line or '"custom_tool_call"' in line:
                    inst, src = hits(names, line)
                    seen |= inst
                    seen_dev |= src
            reads.update(seen)
            dev.update(seen_dev)
    return reads, dev


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="+")
    ap.add_argument("--home", default=str(Path.home()))
    a = ap.parse_args(argv)
    home = Path(a.home)
    calls, creads, cdev = claude_counts(set(a.names), home / ".claude/projects")
    xreads, xdev = codex_counts(set(a.names), [home / ".codex/sessions", home / ".codex/archived_sessions"])
    print("| skill | Claude Skill 调用 | Claude 读取已安装 | Codex 读取已安装 | 源码路径读取（两端） |\n|---|---|---|---|---|")
    for n in sorted(a.names, key=lambda n: -(calls[n] + creads[n] + xreads[n])):
        print(f"| {n} | {calls[n]} | {creads[n]} | {xreads[n]} | {cdev[n] + xdev[n]} |")
    print("\n数字是会话数（Skill 调用是次数）。0 次只说明这段记录里没人用，不等于可以删：先查是否被其他 skill 按路径读取。")


if __name__ == "__main__":
    main()
