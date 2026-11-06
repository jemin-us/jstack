# 面向 agent 的 spec / ticket 模板调研

调研日期：2026-11-06。以下结论来自经过交叉核验的一手文档：Kiro、Anthropic、OpenAI、GitHub 的官方文档，以及一篇预印本。Spec Kit、BMAD、PR-FAQ、Shape Up 以及中文团队的惯例，本轮没有找到通过核验的证据，所以不纳入结论。

## 结论

- **ticket 最小骨架**：三家官方建议可以合成一个骨架，包括目标或问题（含症状）、上下文（涉及的模块或文件）、约束和不做的范围、Done when（可执行命令加期望输出），以及阻塞关系。
  - OpenAI Codex 用四段式：Goal / Context / Constraints / Done when。
  - GitHub 建议把 issue 本身写成 prompt。
  - Anthropic 建议点名文件、写出症状、说明"修好是什么样"。
  - 来源：[Codex best practices](https://developers.openai.com/codex/learn/best-practices)、[Copilot coding agent best practices](https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks)、[Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- **完成判定要可运行**：Anthropic 要求给 agent 一个能返回 pass/fail 的检查。OpenAI ExecPlan 的写法是 "run <test command> and expect <N> passed; the new test fails before the change and passes after"。来源：[ExecPlan](https://developers.openai.com/cookbook/articles/codex_exec_plans)，该页已归档。
- **ticket 要能单独执行**：ExecPlan 要求计划自包含，一个不了解仓库的人只看它就能完成。对 jstack 来说这一条是硬性要求，因为每张 ticket 交给一个没有对话上下文的 subagent 执行。
- **需求可以用 EARS 记法**：格式是 `WHEN <条件> THE SYSTEM SHALL <行为>`。Kiro 说这种写法可测试，但这是厂商自己的说法，没有实证。来源：[Kiro specs](https://kiro.dev/docs/specs/)
- **bug 用另一套结构**：Kiro 的 `bugfix.md` 分三段：当前行为、期望行为、必须保持不变的行为。
- **阻塞关系用 GitHub 原生 dependencies**：该功能 2025-08 正式发布。可以用 `gh issue create --blocked-by`、`gh issue edit --add-blocked-by` 设置，用 `is:blocked` 搜索。每种关系最多 50 条。本机 gh 2.103.3 已经支持这些参数。来源：[changelog](https://github.blog/changelog/2025-08-21-dependencies-on-issues/)、[gh CLI changelog](https://github.blog/changelog/2026-06-10-manage-sub-issues-types-and-dependencies-from-github-cli/)
- **只靠测试做验收不够**：ImpossibleBench 让测试和规格冲突，结果 GPT-5 在两个 SWE-bench 变体上分别有 54% 和 76% 的情况选择违反规格、让测试通过。所以 ticket 里要同时写清规格层面的行为，并禁止通过修改测试来让验收通过。这项研究是预印本，未经同行评审。来源：[arXiv 2510.20270](https://arxiv.org/pdf/2510.20270)

## 待核实

- gh 对 sub-issue 的支持程度：`--parent` 和 `--add-sub-issue` 两个参数在 2.103.3 的帮助文本里能看到，但哪个版本开始支持、参数名有没有变过，结论有冲突。
- 不同 ticket 粒度对 agent 完成率的影响，没有找到实证。
