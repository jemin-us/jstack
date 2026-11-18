# 规则台账

每条给 agent 的规则一行：放在哪、由什么强制、出处和日期。`reflect` 新增行，`trim` 下线行并写明理由。强制一栏是“无”的规则如果再被违反，下次要往上升一级。

| 规则 | 位置 | 由什么强制 | 出处 | 日期 |
|---|---|---|---|---|
| 生成文件（`.claude-plugin/`、`.agents/`、`plugins/jstack/`）不手改 | AGENTS.md | `make test` 漂移检查 | 仓库约定 | 2026-11-14 |
| 改了会发布的文件要递增 `VERSION` | AGENTS.md | CI `scripts/check_version.py` | 仓库约定 | 2026-11-14 |
| skill 之间只引用对方的 `SKILL.md` | AGENTS.md | `scripts/validate.py` | 仓库约定 | 2026-11-14 |
| 根目录不建 `CLAUDE.md` | AGENTS.md | 无 | 建了会让 Claude Code 不再读 AGENTS.md | 2026-11-14 |
| 合并前本地运行 `claude plugin validate .` | AGENTS.md | Claude PreToolUse hook（`~/.claude/hooks/require-ready-merge.py`） | 仓库约定（trim 第二轮升为 hook） | 2026-11-18 |
| 只有 mode 和 help 自动触发，其余 skill 手动调用或由 mode 读取 | skills/*/SKILL.md | `scripts/validate.py` 检查两端开关一致、每个 skill 都登记在 help 或 mode 单步表 | 用户拍板：照 pstack 只留入口（选 2） | 2026-11-14 |
| 三段汇报的定义只写在 harness | skills/harness/SKILL.md | 无 | trim 第一轮：原来在 6 个 skill 里各写一遍 | 2026-11-14 |
| 审查轮次上限只写在 accept | skills/accept/SKILL.md | 无 | trim 第一轮：原来在 3 个 skill 里各写一遍 | 2026-11-14 |
| 全局规则里不写模型本来就会做的事（先读再改、跑测试等） | 三端全局规则（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.gemini/GEMINI.md`） | 无 | 用户拍板：拿不准的都删（trim 第二轮三端统一） | 2026-11-18 |
| 文风要求写成“不写报告腔”加 NO / OK 例子 | 三端全局规则（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.gemini/GEMINI.md`） | 无 | 用户要求用一个词代替三遍重复（trim 第二轮三端统一） | 2026-11-18 |
| 不用 Jev / typesafe-ai | ~/.codex/AGENTS.md（已删整节） | — | 用户：Jev 不用了 | 2026-11-14 |
| 手动调用 skill 的“触发说法”要原样出现在 mode 的 description 里 | skills/mode/SKILL.md | `scripts/validate.py` | 用户第二次纠正：新增 reflect 时漏补，“沉淀一下”没进 mode；reflect 测试提出、用户同意 | 2026-11-14 |
| 能用小实验或原型定的技术选择先跑，按观察结果给推荐；只有产品和偏好选择交给用户 | skills/brainstorm/SKILL.md | 无 | 同步 pstack 0.15.42 的 sharpen 改动，用户同意 | 2026-11-15 |
| 改 agent 规则或 skill 时同步增删台账 | AGENTS.md | Claude/agy PreToolUse hook（`scripts/hooks/inject_agent_rules.py`）+ AGENTS.md 指针 | trim 第二轮：把“做 Y 前读 X”升级为 hook 注入 | 2026-11-18 |
| 写入 GitHub 前确认活跃 gh 账号写权限 | skills/setup/SKILL.md | `skills/setup/scripts/ensure_push_access.py` | trim 第二轮：同样输入同输出改写成脚本 | 2026-11-18 |
| 停用或移出三端 0 调用全局 skills 与插件 | local/uninstalled-plugins.md | `trim/scripts/inventory.py` + `usage.py` | trim 第二轮：按真实调用清理 16 个 agy skill、Codex pdf 与 4 个 0 调用插件 | 2026-11-18 |
| 提交、推送和创建 PR 不需额外授权；合并等不可逆外部操作须明确授权 | 三端全局规则（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.gemini/GEMINI.md`） | Claude PreToolUse hook（`~/.claude/hooks/require-ready-merge.py`） | 用户明确说明：“提交和推送 PR 不需要我授权 只有合并需要我授权” | 2026-11-18 |
