"""trim 的确定性脚本：盘点、调用统计、消失的行。"""
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"skills/trim/scripts/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inventory, usage, vanished = load("inventory"), load("usage"), load("vanished")


class TrimScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_inventory_counts_only_always_loaded(self):
        self.write("home/.claude/CLAUDE.md", "abc")
        self.write("proj/AGENTS.md", "12345")
        self.write("proj/.claude/rules/always.md", "xx")
        self.write("proj/.claude/rules/scoped.md", "---\npaths: [\"**/*.ts\"]\n---\nyy")
        self.write("proj/skills/auto/SKILL.md", "---\nname: auto\ndescription: 四个字符\n---\n正文")
        self.write("proj/skills/manual/SKILL.md", "---\nname: manual\ndescription: 不该计入\ndisable-model-invocation: true\n---\n")
        rows = inventory.rows(self.root / "proj", [self.root / "proj/skills"], self.root / "home")
        names = {src: n for _, src, n in rows}
        self.assertEqual(names["全局规则 ~/.claude/CLAUDE.md"], 3)
        self.assertEqual(names["项目 AGENTS.md"], 5)
        self.assertEqual(names["description auto"], 4)
        self.assertIn("无 paths: 的规则 .claude/rules/always.md", names)
        self.assertFalse(any("scoped" in s or "manual" in s for s in names))

    def test_usage_ignores_injected_paths_and_splits_installed(self):
        injected = {"type": "user", "message": {"content": "可用 skill：/x/plugins/jstack/skills/spec/SKILL.md"}}
        read_inst = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read",
                     "input": {"file_path": "/h/.claude/plugins/cache/jstack/skills/accept/SKILL.md"}}]}}
        read_src = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read",
                    "input": {"file_path": "/repo/skills/accept/SKILL.md"}}]}}
        call = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "jstack:mode"}}]}}
        self.write("home/.claude/projects/p/a.jsonl", "\n".join(json.dumps(e) for e in [injected, read_inst, read_src, call]))
        calls, reads, dev = usage.claude_counts({"spec", "accept", "mode"}, self.root / "home/.claude/projects")
        self.assertEqual((calls["mode"], reads["accept"], dev["accept"], reads["spec"]), (1, 1, 1, 0))
        self.write("home/.codex/sessions/r.jsonl", "\n".join([
            '{"type":"session_meta","instructions":"/u/.codex/plugins/cache/jstack/skills/tickets/SKILL.md"}',
            '{"type":"function_call","arguments":"cat /u/.codex/plugins/cache/jstack/skills/accept/SKILL.md"}']))
        xreads, _ = usage.codex_counts({"tickets", "accept"}, [self.root / "home/.codex/sessions"])
        self.assertEqual((xreads["accept"], xreads["tickets"]), (1, 0))

    def test_vanished_pair_lists_removed_and_changed_lines(self):
        before = self.write("before.md", "保留\n删掉这行\n改前\n\n")
        after = self.write("after.md", "保留\n改后\n")
        self.assertEqual([t for _, t in vanished.pair_lines(before, after)], ["删掉这行", "改前"])
        out = io.StringIO()
        with redirect_stdout(out):
            vanished.main(["--pair", str(before), str(after)])
        self.assertIn("共 2 行", out.getvalue())


if __name__ == "__main__":
    unittest.main()
