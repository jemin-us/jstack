#!/usr/bin/env python3
"""按 Anthropic skill 指南的硬性规则校验 skill 目录。

用法：validate_skill.py <skill 目录>
存在错误时退出码为 1。
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("缺少 PyYAML，先运行 pip install pyyaml 再校验")
    sys.exit(2)

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK = re.compile(r"(?<![\w/~.])((?:references|scripts|assets)/[\w./-]*\w)")
CJK = re.compile(r"[一-鿿]")
# 中文 description 里允许的小写英文术语；大写开头的产品名、缩写、带 - . _ / 的标识符自动放行
TERMS = {"skill", "skills", "description", "frontmatter", "token", "name", "metadata", "references", "scripts", "assets"}
WORD = re.compile(r"(?<![\w.\-/])[a-z]+(?![\w.\-/])")


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def validate(folder: Path):
    errors, warns = [], []
    skill_md = folder / "SKILL.md"
    # 按目录列表精确比对：macOS 默认大小写不敏感，is_file() 会放过 skill.md
    names = [p.name for p in folder.iterdir()] if folder.is_dir() else []
    if "SKILL.md" not in names:
        near = [n for n in names if n.lower() == "skill.md"]
        errors.append(f"缺少 SKILL.md" + (f"（发现 {near[0]}，需改为 SKILL.md）" if near else ""))
        return errors, warns

    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        errors.append("frontmatter 必须以 --- 开头并以 --- 结束")
        return errors, warns
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        errors.append(f"frontmatter YAML 无效：{e}")
        return errors, warns
    if not isinstance(fm, dict):
        errors.append("frontmatter 必须是键值对")
        return errors, warns
    body = m.group(2)

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        errors.append("缺少 name")
    else:
        if not KEBAB.match(name):
            errors.append(f"name 必须是 kebab-case：{name!r}")
        if name != folder.resolve().name:
            errors.append(f"name {name!r} 与文件夹名 {folder.resolve().name!r} 不一致")
        if "claude" in name.lower() or "anthropic" in name.lower():
            errors.append("name 不能包含保留词 claude / anthropic")

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("缺少 description")
    else:
        if len(desc) > 1024:
            errors.append(f"description 超过 1024 字符（{len(desc)}）")
        # 手动调用的 skill 不靠 description 触发
        if fm.get("disable-model-invocation") is not True and not re.search(r"use when|use for|当|用于|触发|时使用", desc, re.I):
            warns.append("description 没写触发场景（例如“当……时使用”）")
        loose = sorted(set(w for w in WORD.findall(desc) if w not in TERMS))
        if CJK.search(desc) and loose:
            warns.append(f"description 疑似中英混排，确认这些词是否为术语：{', '.join(loose)}")

    comp = fm.get("compatibility")
    if comp is not None and not (isinstance(comp, str) and 1 <= len(comp) <= 500):
        errors.append("compatibility 必须是 1–500 字符的字符串")

    if any("<" in s or ">" in s for s in strings(fm)):
        errors.append("frontmatter 不能包含 < 或 >")

    if any(p.name.lower() == "readme.md" for p in folder.iterdir()):
        errors.append("skill 文件夹内不能放 README.md")

    for link in sorted(set(LINK.findall(body))):
        if not (folder / link).exists():
            errors.append(f"正文引用的文件不存在：{link}")

    words = len(re.findall(r"[A-Za-z0-9_]+", body)) + len(CJK.findall(body))
    if words > 5000:
        warns.append(f"SKILL.md 正文约 {words} 词，超过 5000，把细节移到 references/")

    return errors, warns


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip())
        sys.exit(2)
    errors, warns = validate(Path(sys.argv[1]).expanduser())
    for e in errors:
        print(f"错误：{e}")
    for w in warns:
        print(f"提醒：{w}")
    print("通过" if not errors else f"共 {len(errors)} 个错误")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
