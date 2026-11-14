#!/usr/bin/env python3
"""统计每轮都会加载进上下文的内容各占多少字符。只读。

用法：python3 inventory.py [--project <目录>] [--skills <skill 根目录> ...]
"""
import argparse
from pathlib import Path
import re


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def description(fm):
    m = re.search(r"^description:\s*(.*)$", fm, re.M)
    return m.group(1).strip().strip('"') if m else ""


def rows(project, skill_roots, home):
    out = []
    for client, rel in [("Claude Code", ".claude/CLAUDE.md"), ("Codex", ".codex/AGENTS.md")]:
        p = home / rel
        if p.is_file():
            out.append((client, f"全局规则 ~/{rel}", len(p.read_text(encoding="utf-8"))))
    for name, clients in [("AGENTS.md", "两端"), ("CLAUDE.md", "Claude Code")]:
        p = project / name
        if p.is_file():
            out.append((clients, f"项目 {name}", len(p.read_text(encoding="utf-8"))))
    rules = project / ".claude" / "rules"
    if rules.is_dir():
        for p in sorted(rules.rglob("*.md")):
            text = p.read_text(encoding="utf-8")
            if not re.search(r"^paths:", frontmatter(text), re.M):
                out.append(("Claude Code", f"无 paths: 的规则 {p.relative_to(project)}", len(text)))
    for root in skill_roots:
        for p in sorted(root.glob("*/SKILL.md")):
            fm = frontmatter(p.read_text(encoding="utf-8"))
            if re.search(r"^disable-model-invocation:\s*true", fm, re.M):
                continue
            out.append(("两端", f"description {p.parent.name}", len(description(fm))))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default=".")
    ap.add_argument("--skills", nargs="*", default=None, help="skill 根目录，默认 <项目>/skills")
    ap.add_argument("--home", default=str(Path.home()))
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    roots = [Path(r) for r in a.skills] if a.skills is not None else [project / "skills"]
    data = rows(project, roots, Path(a.home))
    print("| 端 | 来源 | 字符数 |\n|---|---|---|")
    for client, src, n in sorted(data, key=lambda r: -r[2]):
        print(f"| {client} | {src} | {n} |")
    print(f"\n合计 {sum(r[2] for r in data)} 字符。只统计你能维护的内容；客户端系统提示词、其他插件和 Codex 自动生成的 memory 不在内。")


if __name__ == "__main__":
    main()
