# frontmatter 与 description

拿不准某个 frontmatter 字段，或 description 某种写法好不好时读取本文件。

## 字段

| 字段 | 必填 | 规则 |
|---|---|---|
| `name` | 是 | kebab-case，与文件夹名一致，不含 `claude`、`anthropic` |
| `description` | 是 | 不超过 1024 字符，不含 `<`、`>`；含空格加 `#`（如 `实现 #42`）时整条加双引号，否则 YAML 从 `#` 起截断 |
| `license` | 否 | 开源时填写，例如 `MIT`、`Apache-2.0` |
| `compatibility` | 否 | 1–500 字符，说明运行环境要求，例如依赖、网络、适用产品 |
| `allowed-tools` | 否 | 限制可用工具，例如 `"Bash(python:*) WebFetch"` |
| `metadata` | 否 | 自定义键值，常用 `version`、`author` |
| `disable-model-invocation` | 否 | Claude Code 专用。`true` 表示手动调用，description 不进入上下文 |

frontmatter 会进入系统提示词，所以不能包含尖括号和可执行代码。

## description 的例子

好的例子：

```
当任务涉及 PostgreSQL 建模、表结构设计、DDL、迁移方案、数据字典或 ER 图时使用。按命名和范式规则产出表结构和迁移脚本。
```

```
当用户要求审查 Shop4 Web 的变更、PR、模块或页面时使用。按审查清单逐项检查并列出问题和所在行。开发自检使用 shop4-web-development。
```

手动调用的 skill：

```
在项目内新建和清理 git worktree 与分支。implement、diagnosing-bugs 改代码前读取，不单独使用。
```

差的例子：

| 写法 | 问题 |
|---|---|
| `帮助处理项目。` | 太宽泛，无法判断何时触发 |
| `构建一套完善的多页面文档体系。` | 只写了做什么，没写触发场景 |
| `当任务涉及 Figma 时使用。` | 只写了触发场景，没写做什么 |
| `实现带层级关系的 Project 实体模型。` | 写的是内部实现，用户不会这么说 |
| `处理文档。` | 范围太大，容易误触发；应收窄为"审查 PDF 合同" |
| `当用户 asks for design specs 时使用。` | 中英混排 |
