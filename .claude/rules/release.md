# 发布 jstack

两端都从 GitHub 仓库 `jemin-us/jstack` 安装插件。合并进 `main` 就是发布。

## 发布前

- PR 上的 CI 会检查插件结构和版本号，失败时先修好再合并。
- CI 不跑 `claude plugin validate .`（需要 Claude CLI），合并前在本地运行一次，通过后再合并。

## 发布后

两端各自更新，Claude Code 要重启会话才生效：

```bash
claude plugin marketplace update jstack && claude plugin update jstack@jstack
codex plugin marketplace upgrade jstack && codex plugin add jstack@jstack
```

## 发布前试用

- Claude Code：`claude --plugin-dir <仓库路径>`，直接从源码加载，不经过缓存。
- Codex：没有对应参数，只能先发布，再按上面的命令更新。
