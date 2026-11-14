---
name: harness
description: jstack 通用说法在 Claude Code 和 Codex 中的对应操作表。其他 jstack skill 需要读取 skill、派 subagent、向用户提问或操作浏览器时读取，不单独使用。
disable-model-invocation: true
---

# Harness adapter

jstack 的 skill 用通用说法书写，按当前 Harness 所在的列执行。整个会话只读一次。

`<jstack 插件目录>` 是本文件所在目录往上两级（本文件位于 `<jstack 插件目录>/skills/harness/SKILL.md`）。读到本文件时确定一次它的绝对路径，之后读取其他 skill、填写 brief 都用这个绝对路径。

| 通用说法 | Claude Code | Codex |
|---|---|---|
| 读取 jstack skill `<name>` | 用 Read 读取 `<jstack 插件目录>/skills/<name>/SKILL.md`；执行任务时照做，只读评估时不执行其中的写操作。`${CLAUDE_PLUGIN_ROOT}` 只在 skill 加载时替换，Bash 里没有这个变量，不要在命令里使用 | 读取 `<jstack 插件目录>/skills/<name>/SKILL.md`；执行任务时照做，只读评估时不执行其中的写操作 |
| 提示用户调用 | `/jstack:<name>` | `$<name>`，或 `/skills` 中选择 |
| 派 subagent 执行 brief | Agent 工具，`subagent_type: general-purpose`，brief 全文放进 prompt | 使用当前实际可用的 spawn/subagent 工具，按其支持的参数传入 brief；不要假定存在名为 worker 的角色 |
| 向用户提问 | AskUserQuestion | 纯文本提问并等待回复 |
| 操作浏览器 | 内置浏览器工具；用户要求用自己的 Chrome 时用 Claude in Chrome | 已安装的 browser 或 chrome 插件；都没有时用 playwright skill |
| 任务列表 | 当前环境提供的任务列表工具 | 当前环境提供的计划工具 |
| 项目指令文件 | `CLAUDE.md`；若项目只有 `AGENTS.md`，Claude Code 会读取它 | `AGENTS.md`；Codex 默认不读 `CLAUDE.md` |

## 三段汇报

汇报写成三段：**改了什么**、**验证了什么**、**还有什么**。每个论断标明"已运行""推断"或"未验证"；"还有什么"没有内容时写"无"。各 skill 在三段里补充自己要求的条目。

## 常见问题

现象：表中的工具在当前环境里不存在。
原因：Harness 版本不同，或者这个工具没有启用。
处理：改用当前环境里用途相同的工具，并在汇报里写明用了哪个；没有可替代的工具时停下，告诉用户缺少什么。

派发前确认实际工具存在并支持参数，记录返回的 agent 标识，再等待该标识的结果。空标识列表不能用于验收。工具不可用时，只有能证明是另一执行者的现有独立渠道才可替代，并记录其任务与返回证据；否则报告独立验收 BLOCKED，不由作者模拟验收者或声称 PASS。
