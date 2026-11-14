# 规则台账

每条给 agent 的规则一行：放在哪、由什么强制、出处和日期。`reflect` 新增行，`trim` 下线行并写明理由。强制一栏是“无”的规则如果再被违反，下次要往上升一级。

| 规则 | 位置 | 由什么强制 | 出处 | 日期 |
|---|---|---|---|---|
| 生成文件（`.claude-plugin/`、`.agents/`、`plugins/jstack/`）不手改 | AGENTS.md | `make test` 漂移检查 | 仓库约定 | 2026-11-14 |
| 改了会发布的文件要递增 `VERSION` | AGENTS.md | CI `scripts/check_version.py` | 仓库约定 | 2026-11-14 |
| skill 之间只引用对方的 `SKILL.md` | AGENTS.md | `scripts/validate.py` | 仓库约定 | 2026-11-14 |
| 根目录不建 `CLAUDE.md` | AGENTS.md | 无 | 建了会让 Claude Code 不再读 AGENTS.md | 2026-11-14 |
| 合并前本地运行 `claude plugin validate .` | AGENTS.md | 无，CI 没有 Claude CLI | 仓库约定 | 2026-11-14 |
| 只有 mode 和 help 自动触发，其余 skill 手动调用或由 mode 读取 | skills/*/SKILL.md | `scripts/validate.py` 检查两端开关一致、每个 skill 都登记在 help 或 mode 单步表 | 用户拍板：照 pstack 只留入口（选 2） | 2026-11-14 |
| 三段汇报的定义只写在 harness | skills/harness/SKILL.md | 无 | trim 第一轮：原来在 6 个 skill 里各写一遍 | 2026-11-14 |
| 审查轮次上限只写在 accept | skills/accept/SKILL.md | 无 | trim 第一轮：原来在 3 个 skill 里各写一遍 | 2026-11-14 |
| 全局规则里不写模型本来就会做的事（先读再改、跑测试等） | 两端全局规则 | 无 | 用户拍板：拿不准的都删 | 2026-11-14 |
| 文风要求写成“不写报告腔”加 NO / OK 例子 | 两端全局规则 | 无 | 用户要求用一个词代替三遍重复 | 2026-11-14 |
| 不用 Jev / typesafe-ai | ~/.codex/AGENTS.md（已删整节） | — | 用户：Jev 不用了 | 2026-11-14 |
