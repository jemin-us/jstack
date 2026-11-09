---
name: j-mode
description: 当用户提出泛化的开发请求时使用，例如“加个功能”“给订单列表加按状态筛选”“改一下这个行为”“修这个 bug”。按 jstack 工作流选 feature 或 bug-fix playbook，依次执行其他 jstack skill 完整推进。请求已指明 ticket 编号、spec 编号或待验收的分支时，使用对应的 implement、to-tickets、accept。
---

# jstack 入口

## 硬性规则

- `<jstack 插件目录>` 是本文件所在目录往上两级（本文件位于 `<jstack 插件目录>/skills/j-mode/SKILL.md`）。开始时确定一次它的绝对路径，之后读取其他 skill、填写 brief 都用这个绝对路径。
- 先读取当前 Harness 的 adapter，整个会话只读一次：[Claude Code](references/harness/claude-code.md)、[Codex](references/harness/codex.md)。下文的"读取 skill""派 subagent""向用户提问"都按 adapter 执行。
- 执行其他 jstack skill 的方式是读取它的 `SKILL.md` 并照做。
- 选定 playbook 后，把它的步骤原样抄进任务列表。不做的步骤保留在列表里，标为"跳过：<原因>"。
- 回复中的每个论断都要标明证据等级：已运行、推断、未验证。自己能跑的检查不交给用户。
- 不在仓库默认分支上 commit，不 push，不开 PR。
- issue 状态只由 j-mode 修改，规则和命令见 [references/issue-state.md](references/issue-state.md)。不加标签。
- 验收结论只来自 accept，作者不能给自己出结论。

## 流程

### 1. 选 playbook

根据用户请求，从下表中选一个：

| playbook | 适用 | 文件 |
|---|---|---|
| feature | 新功能、行为变更，需要 spec 和 ticket | [feature.md](references/playbooks/feature.md) |
| bug-fix | 现有行为出错、报错、性能退化 | [bug-fix.md](references/playbooks/bug-fix.md) |

完成标准：向用户说明选了哪个 playbook，并给出一句理由。两个都不适用时，说明改用哪个 jstack skill，然后直接读取它的 `SKILL.md` 并照做，不再执行下面的步骤。

### 2. 准备分支

- feature：从当前分支新建集成分支 `jstack/spec-<spec 编号>`，各 ticket 的改动最后都合并到这里。spec 编号在 to-spec 发布后才有，所以这一步放到 to-spec 之后执行。
- bug-fix：不切换主目录的分支。修复所用的 worktree 和新分支由 bug-fix playbook 第 1 步建。

完成标准：feature 已切到集成分支；bug-fix 主目录的分支保持不变。

### 3. 执行 playbook

读取选定的 playbook 文件，按步骤执行。每完成一步，就在任务列表里勾掉它。

完成标准：playbook 的每一步都已完成，或已标为跳过并写明原因。

### 4. 收尾

按以下三段汇报：

```markdown
**改了什么**
- 每张 ticket（或这次修复）：行为变化、commit 范围

**验证了什么**
- 每张 ticket 的 accept 结论（PASS / PASS+NOTES / FAIL）和关键证据（已运行）

**还有什么**
- 受阻的验收检查，以及原因
- subagent 做出的假设、选定的测试接缝
- 仍为 open 的 issue 及其状态（验收失败 / 待人工验收）
- 跳过的步骤和原因
```

## 示例

用户说："/jstack:j-mode 给订单列表加按状态筛选"

执行：选择 feature；用 brainstorm 追问两轮；用 to-spec 发布 spec #12，新建分支 `jstack/spec-12`；用 to-tickets 拆出互不阻塞的 #13、#14；两张在各自的 worktree 里并行实现；#13 验收 PASS 后合并；#14 第一次 accept 判 FAIL，带上失败输出重新派一次 subagent，第二次判 PASS 后合并；集成分支全量测试通过。

结果：#13、#14 评论了验收结论并关闭，#12 随之关闭；按三段式汇报。

## 常见问题

现象：同一张 ticket 第二次 accept 仍为 FAIL。
原因：ticket 切分有问题，或者验收检查本身写错了。
处理：停止后续 ticket，把两次 FAIL 的证据交给用户，由用户决定是修改 ticket 还是自己介入。
