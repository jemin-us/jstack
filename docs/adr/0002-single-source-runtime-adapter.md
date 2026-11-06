# 一份源码 + 运行时 adapter，不打包 agents、不生成副本

两个 Harness 共用同一份 `skills/` 源码。工具名等差异写在 `references/harness/<harness>.md` 这类 adapter 文档里，模型在运行时查表处理。这里没有照搬 pstack 的做法，pstack 是为每个 Harness 生成一份副本。插件里也不放 `agents/`：Codex 插件不能打包 agent，所以 subagent 的说明以 brief 形式写进 skill 的 `references/`，再由 Harness 内置的通用 agent 执行。只有当两边出现一份源码写不了的差异时，才引入生成器。

## Considered Options

- pstack 方式：一份源码加生成脚本，按 Harness 输出副本。没有采用，因为现在没有需要改写正文的差异，生成器和 CI 新鲜度检查都是额外维护负担。
- 生成 Codex 的 `~/.codex/agents/*.toml`，再用安装脚本复制过去。没有采用，因为这样要多维护一套安装步骤，两边的行为也会分叉。
