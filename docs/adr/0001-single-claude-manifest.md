# 只用 .claude-plugin/plugin.json，不加根目录 plugin.json

jstack 只放一份 `.claude-plugin/plugin.json`，Claude Code 直接读取它，Codex 也通过 legacy 兼容路径读取它。不加 Codex 推荐的根目录 `plugin.json`（agent-plugins.org schema）。原因是根目录 `plugin.json` 只要声明了 `$schema`，Codex 就会切到 portable 格式。portable 格式会忽略 Claude manifest，不加载 hooks，也不转换 `commands/`，MCP 改读另一种格式的 `mcp.json`。依据见 `docs/research/claude-codex-plugin-compat.md`，源码位置在 `codex-rs/utils/plugins/src/plugin_namespace.rs` 和 `core-plugins/src/loader.rs`。

## Consequences

Codex 如果移除 legacy 兼容路径，需要重新评估这个决定。
