# 发布 jstack

两端都从 GitHub 仓库 `jemin-us/jstack` 安装插件。合并进 `main` 就是发布。

## 发布前

- PR 只要改了 `skills/` 或 `.claude-plugin/`，就在同一个 PR 里递增 `.claude-plugin/plugin.json` 的 `version`。两端的缓存目录按版本号命名，版本号不变时，更新命令可能拉不到新内容。
- 运行 `python3 scripts/validate.py` 和 `claude plugin validate .`，两条都通过后再合并。

## 发布后

两端各自更新，Claude Code 要重启会话才生效：

```bash
claude plugin marketplace update jstack && claude plugin update jstack@jstack
codex plugin marketplace upgrade jstack && codex plugin add jstack@jstack
```

## 发布前试用

- Claude Code：`claude --plugin-dir <仓库路径>`，直接从源码加载，不经过缓存。
- Codex：没有对应参数，只能先发布，再按上面的命令更新。
