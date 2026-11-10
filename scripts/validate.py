#!/usr/bin/env python3
"""校验 jstack 插件结构。用法：python3 scripts/validate.py [插件根目录]。失败时退出码为 1。"""
import json
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools",
                "disable-model-invocation"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)#\s]+)")
PRIVATE_PATH_RE = re.compile(r"skills/([a-z0-9]+(?:-[a-z0-9]+)*)/(references|scripts|assets|agents)/")


def is_skill_entry(dest, skills_root):
    """dest 是否为某个 skill 的 SKILL.md。SKILL.md 是 skill 唯一的公开接口。"""
    return dest.name == "SKILL.md" and dest.parent.parent == skills_root


def frontmatter(text):
    """返回 (顶层键 -> 原始值) 字典；没有 frontmatter 时返回 None。"""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    keys = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            keys[m.group(1)] = m.group(2).strip()
    return keys


def check_skill(d):
    errs = []
    skill_md = d / "SKILL.md"
    if not skill_md.is_file():
        return [f"{d.name}: 缺少 SKILL.md"]
    fm = frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm is None:
        return [f"{d.name}: SKILL.md 缺少 --- 包裹的 frontmatter"]
    name, desc = fm.get("name", ""), fm.get("description", "")
    if name != d.name:
        errs.append(f"{d.name}: name '{name}' 与目录名不一致")
    if not NAME_RE.match(name) or len(name) > 64:
        errs.append(f"{d.name}: name 必须是 1-64 位小写 kebab-case")
    if not 1 <= len(desc) <= 1024:
        errs.append(f"{d.name}: description 长度须为 1-1024")
    if "<" in desc or ">" in desc:
        errs.append(f"{d.name}: description 不能含 < 或 >")
    if re.search(r":\s", desc):
        errs.append(f"{d.name}: description 含 ': '，YAML 会解析出错")
    if desc[:1] not in "\"'" and re.search(r"\s#", desc):
        errs.append(f"{d.name}: description 含空格加 #，YAML 会从这里截断，给整条 description 加双引号")
    extra = set(fm) - ALLOWED_KEYS
    if extra:
        errs.append(f"{d.name}: frontmatter 含不允许的字段 {sorted(extra)}")
    # 两端的自动调用设置必须一致：Claude Code 看 disable-model-invocation，Codex 看 allow_implicit_invocation
    manual = fm.get("disable-model-invocation") == "true"
    want = "false" if manual else "true"
    yaml = d / "agents" / "openai.yaml"
    m = re.search(r"allow_implicit_invocation:\s*(\S+)", yaml.read_text(encoding="utf-8")) if yaml.is_file() else None
    if not m or m.group(1) != want:
        got = m.group(1) if m else "未设置"
        errs.append(f"{d.name}: 两处设置不一致，SKILL.md {'有' if manual else '没有'} disable-model-invocation: true，"
                    f"agents/openai.yaml 的 allow_implicit_invocation 须为 {want}（当前为 {got}）")
    for md in d.rglob("*.md"):
        # 代码块里的链接是模板示例，不是真实链接
        text = re.sub(r"^```.*?^```", "", md.read_text(encoding="utf-8"), flags=re.S | re.M)
        for target in LINK_RE.findall(text):
            if "://" in target or target.startswith("mailto:"):
                continue
            dest = (md.parent / target).resolve()
            if not dest.exists():
                errs.append(f"{md.relative_to(d.parent)}: 链接指向不存在的文件 {target}")
            elif not dest.is_relative_to(d.resolve()) and not is_skill_entry(dest, d.parent.resolve()):
                errs.append(f"{md.relative_to(d.parent)}: 链接 {target} 越过了 skill 边界，"
                            f"只能链接其他 skill 的 SKILL.md")
        # 纯文本路径（包括代码块里的）同样不能指向其他 skill 的内部文件
        for other, sub in PRIVATE_PATH_RE.findall(md.read_text(encoding="utf-8")):
            if other != d.name:
                errs.append(f"{md.relative_to(d.parent)}: 路径 skills/{other}/{sub}/ 指向其他 skill 的内部文件，"
                            f"只能引用 skills/{other}/SKILL.md")
    return errs


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    errs = []
    manifest = root / ".claude-plugin" / "plugin.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("name") != "jstack" or not data.get("version"):
            errs.append("plugin.json: name 须为 jstack 且包含 version")
    except (OSError, json.JSONDecodeError) as e:
        errs.append(f"plugin.json: 无法读取 ({e})")
    if (root / "plugin.json").exists():
        errs.append("根目录不能有 plugin.json，会让 Codex 忽略 .claude-plugin")
    skills = sorted(p for p in (root / "skills").iterdir() if p.is_dir()) if (root / "skills").is_dir() else []
    if not skills:
        errs.append("skills/ 下没有 skill")
    for d in skills:
        errs += check_skill(d)
    help_md = root / "skills" / "help" / "SKILL.md"
    if help_md.is_file():
        help_text = help_md.read_text(encoding="utf-8")
        for d in skills:
            if d.name != "help" and f"](../{d.name}/SKILL.md)" not in help_text:
                errs.append(f"help: 地图里没有 {d.name}，新增 skill 后要登记")
    for e in errs:
        print(f"✗ {e}")
    print(f"{'失败' if errs else '通过'}：{len(skills)} 个 skill，{len(errs)} 个问题")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
