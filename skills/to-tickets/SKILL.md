---
name: to-tickets
description: "当用户要求把已有的 spec 或指明编号的 spec issue 拆成 ticket 时使用，例如“把 #12 拆成 ticket”。规划切分、实现顺序和阻塞关系，并发布为 GitHub issue。还没有 spec 时使用 to-spec；泛化的新功能请求使用 j-mode。"
---

# 拆 ticket

## 硬性规则

- 切分方案经用户确认之前，不创建任何 issue。
- 每张 ticket 必须自包含：一个没有对话上下文的 subagent，只读这张 ticket 就能开工。
- 每张 ticket 有 1–3 条验收检查，格式为 `` `<命令或操作>` → <期望结果> ``。需要超过 3 条，说明切得太粗，继续拆。
- 每张 ticket 的约束中都写上“不改动已有测试来让验收通过”。
- 不修改 spec issue 本身：不改正文、不关闭。
- 只在 spec 所在的仓库里发布 ticket。需求跨多个仓库时，每个仓库按各自的 spec 分别拆。

## 流程

### 1. 读取配置

在项目目录运行 `gh repo view --json nameWithOwner`，确认 ticket 要发到哪个仓库。报错时提示用户先运行 setup-jstack。

完成标准：拿到 `owner/repo`。

### 2. 读取 spec

用户给出 spec issue 编号或链接时，读取全文和全部评论，命令见 [references/github.md](references/github.md)。用户没给时，向用户索要，不要猜。

再浏览 spec 涉及的代码，弄清现有结构、入口文件和相关测试。

完成标准：能说出 spec 的每条行为由哪部分代码承载；spec 的“待定”一节为空。待定不为空时停止，提示用户先回到 to-spec 补全。

### 3. 起草切分方案

按以下规则切分：

- **垂直切片**：每张 ticket 打通一条窄而完整的路径，涉及的各层（数据、接口、界面、测试）都要包括，完成后能单独演示或验证。不按层横切。
- **单个上下文窗口**：每张 ticket 的工作量，一个 subagent 在一个上下文窗口内能做完。
- **先做 prefactor**：需要先调整现有结构才好实现的，单独成一张 ticket，排在最前。
- **减少并行冲突**：没有阻塞关系的 ticket 会并行实现，应当改动不同的模块。两张 ticket 必然要改同一批文件时，给它们加一条阻塞关系，让它们先后进行。
- **大范围机械改动用 expand–contract**：例如改列名、改共享类型这类一处改动波及大量调用方的情况。先 expand（新旧形式并存），再按包或目录分批迁移调用方，每批一张 ticket，最后 contract（删除旧形式）。

为每张 ticket 写明它被哪些 ticket 阻塞。没有阻塞的可以立即开工。

完成标准：每条 spec 行为都落到至少一张 ticket；每张 ticket 都写得出 1–3 条验收检查。

### 4. 和用户确认

按编号列出方案，每张写明三项：

- **标题**：中文，说明交付什么。
- **被阻塞于**：编号列表，或“无”。
- **交付行为**：完成后端到端能用的行为。

向用户提问：粒度是否合适？阻塞关系是否只保留了真正的依赖？有没有需要合并或继续拆的？按反馈修改，直到用户明确同意。

完成标准：用户明确同意当前方案。

### 5. 写 ticket 正文

按 [references/ticket-template.md](references/ticket-template.md) 为每张 ticket 写正文。写完逐张自查：

- 只读这张 ticket，不看对话和其他 ticket，能否开工？
- 验收检查能直接运行吗？是否优先写了“改动前失败、改动后通过”的检查？

完成标准：每张 ticket 都通过上面两项自查。

### 6. 按依赖顺序发布

先发布阻塞别人的 ticket，这样后发布的 ticket 才能引用前面的编号。每张 ticket 的发布要求：

- 用 `--parent <spec 编号>` 挂到 spec 下，成为子 issue；
- 用 `--blocked-by <编号>` 写入阻塞关系。

命令见 [references/github.md](references/github.md)。

完成标准：所有 ticket 都已创建，都是 spec 的子 issue，阻塞关系与确认的方案一致。

### 7. 收尾

列出已创建的 ticket，每张写编号、标题和被阻塞于。提示下一步：用 j-mode 执行 feature playbook，或者按顺序逐张调用 implement。

## 示例

用户说：“把 #12 拆成 ticket。”

执行：

1. 读取 #12 全文和评论，并浏览订单模块的代码。
2. 起草 3 张 ticket：
   - ① 抽出价格计算函数，属于 prefactor；
   - ② 下单时应用优惠码，被 ① 阻塞；
   - ③ 订单详情页显示优惠金额，被 ② 阻塞。
3. 用户确认后按 ①②③ 的顺序发布。

结果：#13、#14、#15 都挂在 #12 下，并带有阻塞关系。

## 常见问题

现象：`gh issue create` 报错 `unknown flag: --parent` 或 `--blocked-by`。
原因：gh 版本太旧。
处理：停止发布，提示用户升级 gh，或者运行 setup-jstack 检查环境。已经创建的 ticket 列出来告诉用户，不要重复创建。

现象：发布到一半失败。
原因：网络中断、权限不足等。
处理：按 [references/github.md](references/github.md) 的补救命令列出 spec 下已经创建的子 issue，只补发缺少的那几张，并补上阻塞关系。
