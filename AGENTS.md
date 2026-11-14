# jstack 仓库指南

Claude Code 和 Codex 共用这份指南，两端都直接读取 `AGENTS.md`，不另建 `CLAUDE.md`。

## 项目

jstack 是个人工程工作流插件，Claude Code 和 Codex 共用 `skills/` 下的同一份源码。

## 仓库结构

- `skills/`：skill 源码，唯一需要手改的 skill 内容。
- `VERSION`：版本号的唯一来源。
- `scripts/build_metadata.py`：从 `VERSION` 和 `skills/` 生成下面这些文件。
- 生成文件，不要手改：
  - `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`：Claude Code 插件和 marketplace。
  - `.agents/plugins/marketplace.json`：Codex marketplace，指向 `plugins/jstack`。
  - `plugins/jstack/`：Codex 插件，`skills/` 的逐字节镜像加 `.codex-plugin/plugin.json`。
- `scripts/check_version.py`：CI 用，改了会发布的文件时要求 `VERSION` 递增。

## 命令

```bash
make test        # validate + 生成文件漂移检查，CI 跑的就是它
make regenerate  # 改了 VERSION 或 skills/ 后运行，生成结果和源文件一起提交
```

## 开发规则

- 改 `skills/` 或 `VERSION` 后运行 `make regenerate`，再运行 `make test`。
- skill 之间只能引用对方的 `SKILL.md`，不能引用对方的 `references/`、`scripts/` 等内部文件；多个 skill 共用的内容抽成单独的 skill。`scripts/validate.py` 会检查这一条。

## 发布

两端都从 GitHub 仓库 `jemin-us/jstack` 安装插件。合并进 `main` 就是发布。

发布前：

- PR 上的 CI 会运行 `make test` 并检查版本号，失败时先修好再合并。
- CI 不跑 `claude plugin validate .`（需要 Claude CLI），合并前在本地运行一次，通过后再合并。

发布后两端各自更新，Claude Code 要重启会话才生效：

```bash
claude plugin marketplace update jstack && claude plugin update jstack@jstack
codex plugin marketplace upgrade jstack && codex plugin add jstack@jstack
```

发布前试用：

- Claude Code：`claude --plugin-dir <仓库路径>`，直接从源码加载，不经过缓存。
- Codex：没有对应参数，只能先发布，再按上面的命令更新。
