"""trim 的确定性脚本：盘点、调用统计、消失的行。"""
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel_dir="skills/trim/scripts"):
    p = ROOT / rel_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inventory, usage, vanished = load("inventory"), load("usage"), load("vanished")
inject_rules = load("inject_agent_rules", "scripts/hooks")
sys.path.insert(0, str(ROOT / "skills/setup/scripts"))
ensure_push_access = load("ensure_push_access", "skills/setup/scripts")


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
        self.write("home/.gemini/GEMINI.md", "wxyz")
        self.write("proj/AGENTS.md", "12345")
        self.write("proj/.claude/rules/always.md", "xx")
        self.write("proj/.claude/rules/scoped.md", "---\npaths: [\"**/*.ts\"]\n---\nyy")
        self.write("proj/skills/auto/SKILL.md", "---\nname: auto\ndescription: 四个字符\n---\n正文")
        self.write("proj/skills/multiline/SKILL.md", "---\nname: multiline\ndescription: >-\n  第一行\n  第二行\n---\n正文")
        self.write("proj/skills/manual/SKILL.md", "---\nname: manual\ndescription: 不该计入\ndisable-model-invocation: true\n---\n")
        rows = inventory.rows(self.root / "proj", [self.root / "proj/skills"], self.root / "home")
        names = {src: n for _, src, n in rows}
        self.assertEqual(names["全局规则 ~/.claude/CLAUDE.md"], 3)
        self.assertEqual(names["全局规则 ~/.gemini/GEMINI.md"], 4)
        self.assertEqual(names["项目 AGENTS.md"], 5)
        self.assertEqual(names["description auto"], 4)
        self.assertEqual(names["description multiline"], len("第一行 第二行"))
        self.assertIn("无 paths: 的规则 .claude/rules/always.md", names)
        self.assertFalse(any("scoped" in s or "manual" in s for s in names))

    def test_inventory_reports_globs_that_match_nothing(self):
        self.write("proj/src/a.ts", "")
        self.write("proj/.claude/rules/ts.md", "---\npaths: [\"src/**/*.ts\"]\n---\n")
        self.write("proj/.claude/rules/old.md", "---\npaths: [\"lib/**/*.js\"]\n---\n")
        self.write("proj/.claude/rules/block.md", "---\npaths:\n  - src/**/*.ts\n  - \"lib/**\"\n---\n")
        self.write("proj/.claude/rules/flat.md", "---\npaths:\n- src/**/*.ts\n- vendor/**\n---\n")
        self.assertEqual(sorted(inventory.dead_globs(self.root / "proj")),
                         [(".claude/rules/block.md", "lib/**"), (".claude/rules/flat.md", "vendor/**"), (".claude/rules/old.md", "lib/**/*.js")])

    def test_usage_ignores_injected_paths_and_splits_installed(self):
        injected = {"type": "user", "message": {"content": "可用 skill：/x/plugins/jstack/skills/spec/SKILL.md"}}
        read_inst = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read",
                     "input": {"file_path": "/h/.claude/plugins/cache/jstack/skills/accept/SKILL.md"}}]}}
        read_src = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read",
                    "input": {"file_path": "/repo/skills/accept/SKILL.md"}}]}}
        call = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "jstack:mode"}}]}}
        self.write("home/.claude/projects/p/a.jsonl", "\n".join(json.dumps(e) for e in [injected, read_inst, read_src, call]))
        self.write("home/.claude/projects/p/b.jsonl", "\n".join(json.dumps(e) for e in [
            {"type": "user", "message": {"content": "<command-name>/jstack:accept</command-name>"}},
            {"type": "user", "message": {"content": "<command-name>/help</command-name>"}},
            {"type": "user", "isSidechain": True, "message": {"content": "brief 引用 <command-name>/jstack:mode</command-name>"}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "<command-name>/jstack:spec</command-name>"}]}}]))
        calls, reads, dev = usage.claude_counts({"spec", "accept", "mode", "help"}, self.root / "home/.claude/projects")
        self.assertEqual((calls["mode"], calls["accept"], calls["help"], calls["spec"], reads["accept"], dev["accept"], reads["spec"]), (1, 1, 0, 0, 1, 1, 0))
        self.write("home/.codex/sessions/r.jsonl", "\n".join([
            '{"type":"session_meta","instructions":"/u/.codex/plugins/cache/jstack/skills/tickets/SKILL.md"}',
            '{"type":"function_call","arguments":"cat /u/.codex/plugins/cache/jstack/skills/accept/SKILL.md"}',
            '{"type":"message","role":"user","content":"$accept 当前分支，别用 $accept-x"}']))
        xreads, _, xcalls = usage.codex_counts({"tickets", "accept"}, [self.root / "home/.codex/sessions"])
        self.assertEqual((xreads["accept"], xreads["tickets"], xcalls["accept"]), (1, 0, 1))

    def test_vanished_git_keeps_deleted_lines_that_start_with_dashes(self):
        import subprocess
        repo = self.root / "g"
        repo.mkdir()
        run = lambda *a: subprocess.run(a, cwd=repo, check=True, capture_output=True)
        run("git", "init", "-q")
        (repo / "a.md").write_text("保留\n---\n--- 像文件头\n--plugin-dir x\n")
        run("git", "add", ".")
        run("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i")
        (repo / "a.md").write_text("保留\n")
        import os
        cwd = os.getcwd()
        os.chdir(repo)
        try:
            lines = vanished.git_lines("HEAD", [])
        finally:
            os.chdir(cwd)
        self.assertEqual(lines, [("a.md", "---"), ("a.md", "--- 像文件头"), ("a.md", "--plugin-dir x")])

    def test_vanished_pair_lists_removed_and_changed_lines(self):
        before = self.write("before.md", "保留\n删掉这行\n改前\n\n")
        after = self.write("after.md", "保留\n改后\n")
        self.assertEqual([t for _, t in vanished.pair_lines(before, after)], ["删掉这行", "改前"])
        out = io.StringIO()
        with redirect_stdout(out):
            vanished.main(["--pair", str(before), str(after)])
        self.assertIn("共 2 行", out.getvalue())

    def test_usage_counts_agy_transcript_reads(self):
        self.write("home/.gemini/antigravity-cli/brain/c1/.system_generated/logs/transcript.jsonl", "\n".join([
            json.dumps({"tool_calls": [{"name": "read_file", "args": {"Path": "/u/.gemini/skills/webapp-testing/SKILL.md"}}]}),
            json.dumps({"tool_calls": [{"name": "view_file", "args": {"AbsolutePath": "/repo/skills/accept/SKILL.md"}}]}),
            json.dumps({"type": "USER_INPUT", "content": "不要把 /u/.gemini/skills/pdf/SKILL.md 算进去"}),
        ]))
        reads, dev = usage.agy_counts({"webapp-testing", "accept", "pdf"}, [self.root / "home/.gemini/antigravity-cli/brain"])
        self.assertEqual((reads["webapp-testing"], dev["accept"], reads["pdf"], dev["pdf"]), (1, 1, 0, 0))

    def test_inject_agent_rules_hook_first_and_dedup(self):
        marker_dir = self.root / "markers"
        marker_dir.mkdir()
        cc_ev = {"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "AGENTS.md")}, "session_id": "s-test-1"}
        out1 = inject_rules.process_event(cc_ev, marker_dir=marker_dir)
        self.assertIn("docs/agent-rules.md", out1["hookSpecificOutput"]["additionalContext"])
        out2 = inject_rules.process_event(cc_ev, marker_dir=marker_dir)
        self.assertEqual(out2, {})

        agy_ev = {"toolCall": {"name": "edit_file", "args": {"Path": str(ROOT / "skills/mode/SKILL.md")}}, "conversationId": "c-test-1"}
        agy1 = inject_rules.process_event(agy_ev, marker_dir=marker_dir)
        self.assertEqual(agy1["decision"], "allow")
        self.assertIn("docs/agent-rules.md", agy1["reason"])
        agy2 = inject_rules.process_event(agy_ev, marker_dir=marker_dir)
        self.assertEqual(agy2, {"decision": "allow"})

        other_ev = {"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "README.md")}, "session_id": "s-test-2"}
        self.assertEqual(inject_rules.process_event(other_ev, marker_dir=marker_dir), {})

    def test_ensure_push_access_switches_account_when_needed(self):
        status_text = (
            "github.com\n"
            "  ✓ Logged in to github.com account reader (keyring)\n"
            "  - Active account: true\n"
            "  ✓ Logged in to github.com account writer (keyring)\n"
            "  - Active account: false\n"
        )
        calls = []

        def fake_run(*cmd, cwd=None):
            calls.append(cmd)
            if cmd[:2] == ("git", "remote"):
                return 0, "origin\thttps://github.com/o/r.git (push)\n"
            if cmd[:3] == ("gh", "repo", "view"):
                # 首次返回 READ，切到 writer 后返回 WRITE
                switched = any(c[:3] == ("gh", "auth", "switch") and c[4] == "writer" for c in calls)
                return 0, "WRITE\n" if switched else "READ\n"
            if cmd[:3] == ("gh", "auth", "status"):
                return 0, status_text
            if cmd[:3] == ("gh", "auth", "switch"):
                return 0, ""
            return 1, ""

        out = io.StringIO()
        with patch.object(ensure_push_access.check_env, "run", side_effect=fake_run), redirect_stdout(out):
            rc = ensure_push_access.ensure_access(self.root)
        self.assertEqual(rc, 0)
        self.assertIn("switched=writer", out.getvalue())
        self.assertIn("push_access=ok", out.getvalue())


if __name__ == "__main__":
    unittest.main()
