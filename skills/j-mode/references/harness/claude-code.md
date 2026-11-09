# Adapter：Claude Code

jstack 正文用通用说法，在 Claude Code 中按下表执行。

| 通用说法 | Claude Code |
|---|---|
| 调用 jstack skill `<name>` | 用 Read 读取 `<jstack 插件目录>/skills/<name>/SKILL.md` 并照做。`${CLAUDE_PLUGIN_ROOT}` 只在 skill 加载时替换，Bash 里没有这个变量，不要在命令里使用 |
| 提示用户调用 | `/jstack:<name>` |
| 派 subagent 执行 brief | Agent 工具，`subagent_type: general-purpose`，brief 全文放进 prompt |
| 向用户提问 | AskUserQuestion |
| 操作浏览器 | 内置浏览器工具；用户要求用自己的 Chrome 时用 Claude in Chrome |
| 任务列表 | 当前环境提供的任务列表工具 |
| 项目指令文件 | `CLAUDE.md`；若项目只有 `AGENTS.md`，Claude Code 会读取它 |
