# jstack 仓库指南

jstack 是 Claude Code、Codex 和 Antigravity CLI（agy）共用的个人工程工作流插件。三端直接读取 `AGENTS.md`，根目录不建 `CLAUDE.md`（建了会让 Claude Code 不再读 `AGENTS.md`）。

## 结构与生成文件

- 唯一需要手改的源码：`skills/` 与 `VERSION`（版本号唯一来源）。
- 生成文件不手改：`.claude-plugin/`、`.agents/plugins/`、`plugins/jstack/`。

## 开发与校验

- 改了会发布的文件（`skills/`、`.claude-plugin/`、`.agents/`、`plugins/`）须递增 `VERSION`，再运行 `make regenerate && make test`（CI 跑的就是 `make test`），生成结果与源文件一起提交。
- skill 之间只能引用对方的 `SKILL.md`，不能引用 `references/`、`scripts/` 等内部文件；多个 skill 共用的内容抽成单独的 skill。
- 改 `AGENTS.md`、skill 的规则或全局规则时，读 [docs/agent-rules.md](docs/agent-rules.md) 并同步增删对应的行。

## 发布

三端都从 GitHub 仓库 `jemin-us/jstack` 安装插件，合并进 `main` 就是发布。合并前：

- PR 上的 CI（`make test` 与版本号检查）必须通过，失败时先修好再合并。
- CI 不跑 `claude plugin validate .`（需要 Claude CLI），合并前在本地运行一次，通过后再合并。

本地试用、校验或更新已安装的 jstack 插件时，读取 [docs/releasing.md](docs/releasing.md)。
