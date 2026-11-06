# Claude Code 与 Codex 插件 / skills 兼容性调研

调研日期：2026-11-06。来源以官方文档为主，两边文档变化快，使用前复核。

## 结论

同一套 SKILL.md 可以同时被两边加载。两边都遵循 [Agent Skills 开放标准](https://agentskills.io/specification)，插件内都从插件根的 `skills/<name>/SKILL.md` 发现 skill。前提是 frontmatter 只用标准的六个字段。

## 共同基础：Agent Skills 标准

- 一个 skill 是一个目录，至少含 `SKILL.md`，可选 `scripts/`、`references/`、`assets/`。
- frontmatter 只定义六个字段：`name`、`description` 必填；`license`、`compatibility`、`metadata`、`allowed-tools`（experimental）可选。
- `name`：1–64 字符，小写字母、数字、连字符，不能首尾或连续连字符，必须与目录名一致。
- `description`：1–1024 字符。

来源：[agentskills.io/specification](https://agentskills.io/specification)、[Claude skills](https://code.claude.com/docs/en/skills)、[Codex skills](https://developers.openai.com/codex/skills.md)

## 差异

| 项 | Claude Code | Codex |
|---|---|---|
| 插件 manifest | `.claude-plugin/plugin.json`，可省略，只要求 `name` | 根目录 `plugin.json`（schema `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`）；兼容 `.codex-plugin/plugin.json` 和 "Claude-compatible manifests" |
| 插件内 skills | `skills/<dir>/SKILL.md`，调用名 `/<plugin>:<dir>` | `skills/<name>/SKILL.md` |
| marketplace 文件 | `.claude-plugin/marketplace.json`（必填 `name`、`owner`、`plugins[]`，条目必填 `name`、`source`） | `$REPO_ROOT/.agents/plugins/marketplace.json`、`~/.agents/plugins/marketplace.json`，以及兼容路径 `$REPO_ROOT/.claude-plugin/marketplace.json`；本地 `source.path` 必须以 `./` 开头 |
| 非插件 skill 路径 | `.claude/skills`、`~/.claude/skills` | CWD 到仓库根每级的 `.agents/skills`、`~/.agents/skills`、`/etc/codex/skills`；跟随 symlink |
| 专属扩展 | frontmatter 扩展字段：`argument-hint`、`disable-model-invocation`、`context: fork`、`` !`cmd` `` 注入等 | `skills/<name>/agents/openai.yaml`：UI、`policy.allow_implicit_invocation`、`dependencies.tools` |
| 安装 | `claude plugin marketplace add owner/repo` → `claude plugin install <name>@<marketplace>` | 通过 marketplace 安装插件；`$skill-installer` 只适合本地试用 |

来源：[plugins-reference](https://code.claude.com/docs/en/plugins-reference)、[plugin components](https://code.claude.com/docs/en/plugins/components)、[plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)、[Codex plugins/build](https://developers.openai.com/codex/plugins/build.md)

注意：claude.ai 上传、Skills API、`package_skill.py` 遇到标准外字段会报错，不会忽略。

## 更正（源码核实，2026-11-06）

下面"推荐结构"中的根目录 `plugin.json` 不要加。依据 `github.com/openai/codex` 源码（`codex-rs/`）：

- 根目录 `plugin.json` 只要带 agent-plugins.org 的 `$schema`，Codex 就改用 portable 格式，并忽略 `.claude-plugin/plugin.json`（`utils/plugins/src/plugin_namespace.rs`）。portable 格式下有三处变化：hooks 不加载（`loader.rs` 在 AgentPlugin 分支直接返回空）；`commands/` 不转换成 skill；MCP 改读另一种格式的 `mcp.json`。
- 只放 `.claude-plugin/plugin.json` 时，Codex 走 legacy 兼容路径，能识别 `skills/`、`.mcp.json`、`hooks/hooks.json`；`commands/` 会被转换成名为 `source-command-<name>` 的 skill。
- Codex 插件不能打包 subagent。Codex 的自定义 agent 只从 `~/.codex/agents/*.toml` 和 `.codex/agents/*.toml` 加载，格式是 TOML，必填 `name`、`description`、`developer_instructions`。
- 两边的 hooks.json 结构一致，Codex 会同时注入 `PLUGIN_ROOT` 和 `CLAUDE_PLUGIN_ROOT` 两个环境变量。matcher 里的工具名不同：Codex 用 `Bash`、`apply_patch`，`apply_patch` 也可以写成 `Edit`/`Write`。hook 要用户信任之后才会运行。
- 插件内 skill 的命名空间两边相同，都是 `<plugin>:<skill>`。显式调用方式不同：Claude 用 `/jstack:x`，Codex 用 `$` 提及或 `/skills`。
- Codex 默认不读 `CLAUDE.md`。Claude Code 只在目录里没有 `CLAUDE.md` 时才读 `AGENTS.md`。

## 推荐结构（推断，未实测；根目录 plugin.json 已被上面的更正否定）

两边都没有官方的双端模板。下面的布局是根据上面的文档推出来的：

```
.
├── .claude-plugin/
│   ├── plugin.json          # Claude 用，只写 name 等基本字段
│   └── marketplace.json     # source: "./"；Codex 也会读这个兼容路径
├── plugin.json              # Codex 用，agent-plugins.org schema
└── skills/
    └── <name>/
        ├── SKILL.md         # 只用标准六个字段
        └── agents/openai.yaml   # 可选，Codex 专属
```

发布：推到 GitHub 并打 tag。

## 待实测

1. 只放 `.claude-plugin/plugin.json`、不放根目录 `plugin.json` 时，Codex 能否正确加载？Claude Code 会不会忽略根目录的 `plugin.json`？
2. `commands/`、`agents/`、`hooks/`、`.mcp.json` 在 Codex 里是否有对应机制？本次没有核实。目前只能确认 skills 可以共用。
3. 两边的命名空间和调用语法有差异（Claude 用 `/<plugin>:<skill>`，Codex 用 `$skill`），同名 skill 冲突时怎么处理？
4. 两边分别怎么锁定版本（ref/sha、tag）？
