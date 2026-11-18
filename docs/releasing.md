# 本地试用与更新已安装插件

发布后各端更新，Claude Code 要重启会话才生效：

```bash
claude plugin marketplace update jstack && claude plugin update jstack@jstack
codex plugin marketplace upgrade jstack && codex plugin add jstack@jstack
agy plugin install https://github.com/jemin-us/jstack
```

发布前试用：

- Claude Code：`claude --plugin-dir <仓库路径>`，直接从源码加载，不经过缓存。
- Codex：没有对应参数，只能先发布，再按上面的命令更新。
- agy：`agy plugin install <仓库路径>`，自动从 Claude Code 插件转换安装到 `~/.gemini/config/plugins/jstack`（直接对仓库根目录运行 `agy plugin validate` 会报错，需对转换后的目录校验）。
