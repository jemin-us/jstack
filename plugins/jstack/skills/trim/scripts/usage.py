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
import re
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


def typed_command(line, names, plugin):
    """用户亲手输入的 /<插件>:<名称>：只看 type 为 user、content 是字符串的消息。"""
    if '"type":"user"' not in line.replace(" ", "") or "<command-name>" not in line:
        return set()
    try:
        e = json.loads(line)
    except ValueError:
        return set()
    msg = e.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if e.get("type") != "user" or not isinstance(content, str):
        return set()
    found = re.findall(r"<command-name>/" + re.escape(plugin) + r":([\w-]+)</command-name>", content)
    return {n for n in found if n in names}


def claude_counts(names, root, plugin="jstack"):
    calls, reads, dev = Counter(), Counter(), Counter()
    for f in root.glob("**/*.jsonl"):
        seen, seen_dev, called = set(), set(), set()
        for line in open(f, errors="ignore"):
            called |= typed_command(line, names, plugin)
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
                    called.add(skill)
                inst, src = hits(names, json.dumps(inp, ensure_ascii=False))
                seen |= inst
                seen_dev |= src
        reads.update(seen)
        dev.update(seen_dev)
        calls.update(called)
    return calls, reads, dev


def codex_counts(names, roots):
    reads, dev, calls = Counter(), Counter(), Counter()
    for root in roots:
        for f in root.glob("**/*.jsonl"):
            seen, seen_dev, called = set(), set(), set()
            for line in open(f, errors="ignore"):
                if '"role":"user"' in line:
                    called.update(n for n in names if re.search(r"\$" + re.escape(n) + r"(?![\w-])", line))
                if '"function_call"' in line or '"custom_tool_call"' in line:
                    inst, src = hits(names, line)
                    seen |= inst
                    seen_dev |= src
            reads.update(seen)
            dev.update(seen_dev)
            calls.update(called)
    return reads, dev, calls


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="+")
    ap.add_argument("--home", default=str(Path.home()))
    ap.add_argument("--plugin", default="jstack", help="Claude Code 斜杠命令的插件前缀")
    a = ap.parse_args(argv)
    home = Path(a.home)
    calls, creads, cdev = claude_counts(set(a.names), home / ".claude/projects", a.plugin)
    xreads, xdev, xcalls = codex_counts(set(a.names), [home / ".codex/sessions", home / ".codex/archived_sessions"])
    print("| skill | Claude 调用（Skill 工具和 /命令） | Codex 手动调用（$名称） | Claude 读取已安装 | Codex 读取已安装 | 源码路径读取（两端） |\n|---|---|---|---|---|---|")
    for n in sorted(a.names, key=lambda n: -(calls[n] + xcalls[n] + creads[n] + xreads[n])):
        print(f"| {n} | {calls[n]} | {xcalls[n]} | {creads[n]} | {xreads[n]} | {cdev[n] + xdev[n]} |")
    print("\n数字都是会话数。0 次只说明这段记录里没人用，不等于可以删：先查是否被其他 skill 按路径读取。")


if __name__ == "__main__":
    main()
