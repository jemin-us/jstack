#!/usr/bin/env python3
"""从 VERSION 和 skills/ 生成两端的插件清单和 Codex 插件镜像。

用法：
  python3 scripts/build_metadata.py          重新生成
  python3 scripts/build_metadata.py --check  只检查，生成结果与仓库不一致时退出码为 1

生成的文件（不要手改，改源文件后重新生成）：
  .claude-plugin/plugin.json、.claude-plugin/marketplace.json   Claude Code
  .agents/plugins/marketplace.json                               Codex marketplace
  plugins/jstack/.codex-plugin/plugin.json                       Codex 插件清单
  plugins/jstack/skills/                                         skills/ 的逐字节镜像
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "jstack"
OWNER = "jemin-us"
REPO = f"https://github.com/{OWNER}/{NAME}"
DESCRIPTION = "个人工程工作流：需求追问、spec、ticket、实现、独立验收。Claude Code 与 Codex 共用。"
CODEX_ROOT = Path("plugins") / NAME
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def dump(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def manifests(version):
    """返回 {相对路径: 文件字节}，不含镜像。"""
    return {
        Path(".claude-plugin/plugin.json"): dump({
            "name": NAME,
            "version": version,
            "description": DESCRIPTION,
            "author": {"name": OWNER},
        }),
        Path(".claude-plugin/marketplace.json"): dump({
            "name": NAME,
            "owner": {"name": OWNER},
            "plugins": [{
                "name": NAME,
                "source": "./",
                "description": "个人工程工作流：需求追问、spec、ticket、实现、独立验收。",
            }],
        }),
        Path(".agents/plugins/marketplace.json"): dump({
            "name": NAME,
            "interface": {"displayName": NAME},
            "plugins": [{
                "name": NAME,
                "source": {"source": "local", "path": f"./{CODEX_ROOT.as_posix()}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }],
        }),
        CODEX_ROOT / ".codex-plugin/plugin.json": dump({
            "name": NAME,
            "version": version,
            "description": DESCRIPTION,
            "author": {"name": OWNER, "url": f"https://github.com/{OWNER}"},
            "homepage": REPO,
            "repository": REPO,
            "skills": "./skills/",
            "interface": {
                "displayName": NAME,
                "shortDescription": "需求追问、spec、ticket、实现、独立验收",
                "developerName": OWNER,
                "category": "Developer Tools",
                "capabilities": ["Interactive", "Write"],
                "websiteURL": REPO,
            },
        }),
    }


def mirror():
    """返回 {镜像里的相对路径: 源文件字节}，覆盖 skills/ 下所有文件。"""
    src = ROOT / "skills"
    return {
        CODEX_ROOT / "skills" / p.relative_to(src): p.read_bytes()
        for p in sorted(src.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def existing_mirror():
    dst = ROOT / CODEX_ROOT / "skills"
    return {p.relative_to(ROOT) for p in dst.rglob("*") if p.is_file()} if dst.is_dir() else set()


def main():
    check = "--check" in sys.argv[1:]
    try:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as e:
        print(f"✗ 读不到 VERSION：{e}")
        return 1
    if not VERSION_RE.match(version):
        print(f"✗ VERSION '{version}' 不是 x.y.z 格式")
        return 1

    want = {**manifests(version), **mirror()}
    stale = existing_mirror() - set(want)
    differ = [p for p, data in want.items() if not (ROOT / p).is_file() or (ROOT / p).read_bytes() != data]

    if check:
        for p in differ:
            print(f"✗ 与生成结果不一致：{p.as_posix()}")
        for p in sorted(stale):
            print(f"✗ 镜像里多出源中没有的文件：{p.as_posix()}")
        if differ or stale:
            print("运行 make regenerate 后一起提交")
            return 1
        print(f"通过：生成文件与 VERSION {version} 和 skills/ 一致")
        return 0

    for p in differ:
        (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / p).write_bytes(want[p])
    for p in stale:
        (ROOT / p).unlink()
    for d in sorted((ROOT / CODEX_ROOT / "skills").rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    print(f"已生成：更新 {len(differ)} 个文件，删除 {len(stale)} 个镜像残留，版本 {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
