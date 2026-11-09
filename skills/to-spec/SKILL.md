---
name: to-spec
description: 当用户要求把已讨论清楚的需求或讨论结果写成 spec、发布 spec issue 时使用，例如“把讨论结果写成 spec”。需求还不清楚时使用 brainstorm；泛化的新功能请求使用 j-mode；拆 ticket 使用 to-tickets。
---

# 生成 spec

把对话里已经讨论清楚的需求整理成 spec，发布为 GitHub issue。

## 硬性规则

- "待定"不为空时不发布。先把待定项逐条交给用户决定，清空后再继续。
- 发布前必须把 spec 全文给用户确认。用户确认前，不执行任何创建 issue 的命令。
- 正文严格按 [references/spec-template.md](references/spec-template.md) 的章节书写，行为一节每条都用"当…时，系统应…"。

## 流程

### 1. 读取项目配置

在项目目录运行 `gh repo view --json nameWithOwner`，确认 issue 要发到哪个仓库。gh 根据 git remote 识别仓库；报错时提示用户先运行 jstack skill `setup-jstack`。

完成标准：拿到 `owner/repo`。

### 2. 了解代码现状

阅读与需求相关的模块和已有测试。

完成标准：能说出需求会改动哪些模块，以及这些模块现在怎么测试。

### 3. 判断是否跨仓库

需求同时涉及多个仓库（例如前端和后端）时，每个仓库各写一份 spec：

- 后端 spec 负责 API 契约；
- 前端 spec 引用后端 spec 的 issue，不重复契约。

先写并发布后端 spec，拿到链接后再写前端 spec。

完成标准：列出要写 spec 的仓库清单和发布顺序。

### 4. 生成 spec

读取 [references/spec-template.md](references/spec-template.md)，按模板生成中文标题和正文。

完成标准：每个章节都有内容；行为每条都能被验证；"待定"写的是"无"。

"待定"不为空时：只有一两条，直接逐条问用户，按回答更新 spec；需要大范围重新讨论时，停下来建议用户先使用 jstack skill `brainstorm`。

### 5. 用户确认

把标题和正文全文展示给用户，请用户确认或修改。

完成标准：用户明确同意发布。用户提出修改时，改完重新展示。

### 6. 发布

正文写入临时文件后创建 issue：

```bash
f=$(mktemp)  # 正文写进系统临时文件，不放进项目目录
gh issue create --repo <仓库> --title "<中文标题>" --body-file "$f"
```

跨仓库时按第 3 步的顺序逐个发布，前端 spec 发布前把后端 spec 的链接填进正文。

完成标准：每份 spec 都拿到 issue 链接。

### 7. 收尾

向用户报告每份 spec 的 issue 链接，提示下一步使用 jstack skill `to-tickets` 拆成 ticket。

## 示例

用户说："需求聊清楚了，写成 spec 吧。"

执行：
1. `gh repo view` 确认仓库是 `jemin-us/shop`；
2. 阅读订单模块和已有接口测试；
3. 判断只涉及一个仓库；
4. 按模板生成 spec，测试接缝写"在订单 API 层做接口测试"，"待定"为"无"；
5. 展示全文，用户同意；
6. 创建 issue。

结果：返回 issue 链接，并提示运行 `to-tickets`。

## 常见问题

现象：`gh` 报未登录或没有权限。
原因：当前账号未登录，或对目标仓库没有写权限。
处理：停止发布，把报错原文告诉用户，请用户自己完成登录或切换账号。

现象：生成过程中发现行为互相矛盾，或缺少关键决定。
原因：讨论阶段没有覆盖到。
处理：写进"待定"，按第 4 步处理：一两条直接问用户，大范围的回到 `brainstorm`。
