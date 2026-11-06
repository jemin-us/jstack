# AGENTS.md 中的 jstack 配置块

to-spec 和 to-tickets 从这一块读取仓库和标签信息。块从 `## jstack` 开始，到下一个 `## ` 标题或文件末尾结束。

## 模板

```markdown
## jstack

- issue 仓库：<owner/repo>
- spec 标签：`jstack:spec`
- ticket 标签：`jstack:ticket`
- ticket 是 spec 的子 issue；ticket 之间的阻塞关系使用 GitHub 原生 dependency。
```

## 写入规则

- 只替换 `## jstack` 块本身，块外的内容一个字都不改。
- 需求跨多个仓库时，每个仓库各运行一次 setup-jstack，各自写自己的 `owner/repo`。
