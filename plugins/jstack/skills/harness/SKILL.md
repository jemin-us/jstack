---
name: harness
description: jstack 通用说法在 Claude Code、Codex 和 Antigravity CLI（agy）中的对应操作表。其他 jstack skill 需要读取 skill、派 subagent、向用户提问或操作浏览器时读取，不单独使用。
disable-model-invocation: true
---

# Harness adapter

jstack 的 skill 用通用说法书写，按当前 Harness 所在的列执行。整个会话只读一次。

`<jstack 插件目录>` 是本文件所在目录往上两级（本文件位于 `<jstack 插件目录>/skills/harness/SKILL.md`）。读到本文件时确定一次它的绝对路径，之后读取其他 skill、填写 brief 都用这个绝对路径。

| 通用说法 | Claude Code | Codex | agy |
|---|---|---|---|
| 读取 jstack skill `<name>` | 用 Read 读取 `<jstack 插件目录>/skills/<name>/SKILL.md`；执行任务时照做，只读评估时不执行其中的写操作。`${CLAUDE_PLUGIN_ROOT}` 只在 skill 加载时替换，Bash 里没有这个变量，不要在命令里使用 | 读取 `<jstack 插件目录>/skills/<name>/SKILL.md`；执行任务时照做，只读评估时不执行其中的写操作 | 用 `read_file` 读取 `<jstack 插件目录>/skills/<name>/SKILL.md`（已安装插件在 `~/.gemini/config/plugins/jstack`）；执行任务时照做，只读评估时不执行其中的写操作 |
| 提示用户调用 | `/jstack:<name>` | `$<name>`，或 `/skills` 中选择 | `/jstack:<name>`，或 `/skills` 中查看（项目内 `.agents/skills` 加载时为 `/<name>`） |
| 派 subagent 执行 brief | Agent 工具，`subagent_type: general-purpose`，brief 全文放进 prompt | 使用当前实际可用的 spawn/subagent 工具，按其支持的参数传入 brief；不要假定存在名为 worker 的角色 | `invoke_subagent`（需运行命令或改文件时 `TypeName` 填 `self`，纯只读调查可填 `research`），brief 全文放进 `Prompt`；调用后结束当前轮次等待系统唤醒并带回消息，多个并行时可同时调用或用 `run_workflow`，可复用类型用 `define_subagent` |
| 向用户提问 | AskUserQuestion | 纯文本提问并等待回复 | 选择题用 `ask_question`；开放式或简单是否问题用纯文本提问并等待回复 |
| 操作浏览器 | 内置浏览器工具；用户要求用自己的 Chrome 时用 Claude in Chrome | 已安装的 browser 或 chrome 插件；都没有时用 playwright skill | 交互时提示用户用内置 `/browser`（Chrome DevTools subagent）；自动执行且当前无浏览器工具时用内置 `webapp-testing` skill（Playwright） |
| 任务列表 | 当前环境提供的任务列表工具 | 当前环境提供的计划工具 | 没有对应工具（`manage_task` 管理的是后台命令），在回复中写计划 |
| 当前会话记录 | `~/.claude/projects/<项目绝对路径中的 / 换成 ->/<会话 id>.jsonl`，按修改时间取最近几个，核对第一条用户消息 | `~/.codex/sessions/<年>/<月>/<日>/rollout-*.jsonl`，按修改时间取最近几个，核对第一条用户消息 | `~/.gemini/antigravity-cli/brain/<会话 id>/.system_generated/logs/transcript.jsonl`（字段被截断时读同行 `transcript_full.jsonl`）；当前会话直接取环境信息中的 Conversation ID，其他会话按修改时间取最近几个并核对第一条 `USER_INPUT` |
| 项目指令文件 | `CLAUDE.md`；若项目只有 `AGENTS.md`，Claude Code 会读取它 | `AGENTS.md`；Codex 默认不读 `CLAUDE.md` | `AGENTS.md` 和 `GEMINI.md`（同目录共存时都会读取，`AGENTS.md` 在前）；默认不读 `CLAUDE.md` |

## 三段汇报

汇报写成三段：**改了什么**、**验证了什么**、**还有什么**。每个论断标明"已运行""推断"或"未验证"；"还有什么"没有内容时写"无"。各 skill 在三段里补充自己要求的条目。

## 常见问题

现象：表中的工具在当前环境里不存在。
原因：Harness 版本不同，或者这个工具没有启用。
处理：改用当前环境里用途相同的工具，并在汇报里写明用了哪个；没有可替代的工具时停下，告诉用户缺少什么。

派发前确认实际工具存在并支持参数，记录返回的 agent 标识，再等待该标识的结果。空标识列表不能用于验收。工具不可用时，只有能证明是另一执行者的现有独立渠道才可替代，并记录其任务与返回证据；否则报告独立验收 BLOCKED，不由作者模拟验收者或声称 PASS。
