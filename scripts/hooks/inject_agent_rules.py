#!/usr/bin/env python3
"""Claude Code & Antigravity CLI PreToolUse hook：编辑规则或 skill 文件时注入 docs/agent-rules.md。"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DOC = REPO_ROOT / "docs" / "agent-rules.md"
HOME_RULE_FILES = {
    (Path.home() / ".claude" / "CLAUDE.md").resolve(),
    (Path.home() / ".codex" / "AGENTS.md").resolve(),
    (Path.home() / ".gemini" / "GEMINI.md").resolve(),
}


def parse_event(data: dict):
    """返回 (client, tool_name, file_path, session_id)。"""
    if "toolCall" in data:
        tc = data.get("toolCall") or {}
        args = tc.get("args") or {}
        return "agy", tc.get("name", ""), args.get("Path", ""), data.get("conversationId", "")
    inp = data.get("tool_input") or {}
    return "claude", data.get("tool_name", ""), inp.get("file_path", ""), data.get("session_id", "")


def is_target_file(file_path: str, cwd: str = "") -> bool:
    if not file_path:
        return False
    p = Path(file_path).expanduser()
    if not p.is_absolute():
        base = Path(cwd) if cwd else REPO_ROOT
        p = base / p
    resolved = p.resolve()
    if resolved in HOME_RULE_FILES:
        return True
    try:
        rel = resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return False
    if rel == "docs/agent-rules.md":
        return False
    if rel in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        return True
    return rel.startswith("skills/") and rel.endswith(".md")


def allow_output(client: str, message: str = ""):
    if client == "agy":
        out = {"decision": "allow"}
        if message:
            out["reason"] = message
        return out
    if message:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": message,
            }
        }
    return {}


def process_event(data: dict, marker_dir: Path = Path("/tmp")) -> dict:
    client, tool_name, file_path, session_id = parse_event(data)
    if tool_name not in ("Edit", "Write", "MultiEdit", "edit_file", "write_file"):
        return allow_output(client)
    if not is_target_file(file_path, data.get("cwd", "")):
        return allow_output(client)

    marker = None
    if session_id:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id))
        marker = marker_dir / f"jstack-rules-injected-{safe}"
        if marker.exists():
            return allow_output(client)

    if not RULES_DOC.is_file():
        return allow_output(client)

    msg = "修改规则前请核对并同步增删 docs/agent-rules.md 中的台账行：\n\n" + RULES_DOC.read_text(encoding="utf-8")
    if marker:
        marker.write_text("1", encoding="utf-8")
    return allow_output(client, msg)


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        print("{}")
        return 0
    client = "agy" if "toolCall" in data else "claude"
    try:
        out = process_event(data)
    except Exception:
        out = allow_output(client)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
