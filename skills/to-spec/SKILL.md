---
name: to-spec
description: 当任务涉及把已讨论清楚的需求写成 spec、整理需求文档、发布 spec issue 时使用。需求还不清楚时使用 brainstorm；要拆成可执行任务时使用 to-tickets。
disable-model-invocation: true
---

# 生成 spec

把对话里已经讨论清楚的需求整理成 spec，发布为 GitHub issue。

## 硬性规则

- 不追问需求。只整理已经讨论过的内容；发现需求缺口时，写进"待定"。
- "待定"不为空时不发布。先把待定项逐条交给用户决定，清空后再继续。
- 发布前必须把 spec 全文给用户确认。用户确认前，不执行任何创建 issue 的命令。
- 正文严格按 [references/spec-template.md](references/spec-template.md) 的章节书写，行为一节每条都用"当…时，系统应…"。
- 术语使用项目 `GLOSSARY.md` 中的说法；有 ADR 的领域，spec 不得与 ADR 冲突。

## 流程

### 1. 读取项目配置

读取项目 `AGENTS.md` 中的 `## jstack` 块，取出 GitHub 仓库和 spec 标签。

完成标准：拿到仓库名和标签。没有这个块时，停止执行，提示用户先运行 jstack skill `setup-jstack`。

### 2. 了解代码现状

阅读与需求相关的模块、已有测试和 `docs/adr/`。

完成标准：能说出需求会改动哪些模块，以及这些模块现在怎么测试。

### 3. 确认测试接缝

提出测试接缝：在哪一层验证行为，复用哪类已有测试。优先已有接缝，层级尽量高，数量尽量少。向用户提问，确认接缝符合预期。

完成标准：用户确认了测试接缝。

### 4. 判断是否跨仓库

需求同时涉及多个仓库（例如前端和后端）时，每个仓库各写一份 spec：

- 后端 spec 负责 API 契约；
- 前端 spec 引用后端 spec 的 issue，不重复契约。

先写并发布后端 spec，拿到链接后再写前端 spec。

完成标准：列出要写 spec 的仓库清单和发布顺序。

### 5. 生成 spec

读取 [references/spec-template.md](references/spec-template.md)，按模板生成中文标题和正文。

完成标准：每个章节都有内容；行为每条都能被验证；"待定"写的是"无"。"待定"不为空时，向用户逐条提问，按回答更新 spec，直到清空。

### 6. 用户确认

把标题和正文全文展示给用户，请用户确认或修改。

完成标准：用户明确同意发布。用户提出修改时，改完重新展示。

### 7. 发布

正文写入临时文件后创建 issue：

```bash
f=$(mktemp)  # 正文写进系统临时文件，不放进项目目录
gh issue create --repo <仓库> --title "<中文标题>" --label "jstack:spec" --body-file "$f"
```

跨仓库时按第 4 步的顺序逐个发布，前端 spec 发布前把后端 spec 的链接填进正文。

完成标准：每份 spec 都拿到 issue 链接。

### 8. 收尾

向用户报告每份 spec 的 issue 链接，提示下一步使用 jstack skill `to-tickets` 拆成 ticket。

## 示例

用户说："需求聊清楚了，写成 spec 吧。"

执行：
1. 从 `AGENTS.md` 读到仓库 `jemin-us/shop` 和标签 `jstack:spec`；
2. 阅读订单模块和已有接口测试；
3. 提出"在订单 API 层做接口测试"，用户确认；
4. 判断只涉及一个仓库；
5. 按模板生成 spec，"待定"为"无"；
6. 展示全文，用户同意；
7. 创建 issue。

结果：返回 issue 链接，并提示运行 `to-tickets`。

## 常见问题

现象：`gh issue create` 报 `could not add label: 'jstack:spec' not found`。
原因：仓库里还没有这个标签。
处理：提示用户运行 `setup-jstack` 创建标签，不要自行去掉标签后发布。

现象：`gh` 报未登录或没有权限。
原因：当前账号未登录，或对目标仓库没有写权限。
处理：停止发布，把报错原文告诉用户，请用户自己完成登录或切换账号。

现象：生成过程中发现行为互相矛盾，或缺少关键决定。
原因：讨论阶段没有覆盖到。
处理：写进"待定"，按第 5 步向用户提问；需要大范围重新讨论时，建议先使用 `brainstorm`。
