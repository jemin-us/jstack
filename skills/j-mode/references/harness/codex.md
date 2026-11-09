# Adapter：Codex

jstack 正文用通用说法，在 Codex 中按下表执行。

| 通用说法 | Codex |
|---|---|
| 调用 jstack skill `<name>` | 读取 `<jstack 插件目录>/skills/<name>/SKILL.md` 并照做 |
| 提示用户调用 | `$<name>`，或 `/skills` 中选择 |
| 派 subagent 执行 brief | 明确要求 spawn 内置 `worker` agent，brief 全文作为任务说明 |
| 向用户提问 | 纯文本提问并等待回复 |
| 操作浏览器 | 已安装的 browser 或 chrome 插件；都没有时用 playwright skill |
| 任务列表 | 当前环境提供的计划工具 |
| 项目指令文件 | `AGENTS.md`；Codex 默认不读 `CLAUDE.md` |
| worktree 目录 | `.codex/worktrees`，规则见 [worktree.md](../../../implement/references/worktree.md) |
