---
name: j-mode
description: 当任务需要按 jstack 工作流完整推进时使用，包括开发新功能（feature）和修复 bug（bug-fix）。选中 playbook 后按步骤执行其他 jstack skill。只想用其中一步时，直接调用对应的 skill。
disable-model-invocation: true
---

# jstack 入口

## 硬性规则

- 先读取当前 Harness 的 adapter，整个会话只读一次：[Claude Code](references/harness/claude-code.md)、[Codex](references/harness/codex.md)。下文的"读取 skill""派 subagent""向用户提问"都按 adapter 执行。
- 执行其他 jstack skill 的方式是读取它的 `SKILL.md` 并照做，不通过 Harness 的 skill 调用机制。jstack 的 skill 都关闭了自动调用，调用机制会拒绝。
- 选定 playbook 后，把它的步骤原样抄进任务列表。不做的步骤保留在列表里，标为"跳过：<原因>"。
- 回复中的每个论断都要标明证据等级：已运行、推断、未验证。自己能跑的检查不交给用户。
- 只在当前分支 commit，不 push，不开 PR，不关闭 issue。
- 验收结论只来自 accept，作者不能给自己出结论。

## 流程

### 1. 选 playbook

根据用户请求，从下表中选一个：

| playbook | 适用 | 文件 |
|---|---|---|
| feature | 新功能、行为变更，需要 spec 和 ticket | [feature.md](references/playbooks/feature.md) |
| bug-fix | 现有行为出错、报错、性能退化 | [bug-fix.md](references/playbooks/bug-fix.md) |

完成标准：向用户说明选了哪个 playbook，并给出一句理由。两个都不适用时，告诉用户直接调用哪个 jstack skill，然后结束。

### 2. 准备分支

运行 `git branch --show-current`。如果当前是仓库默认分支，先新建分支再开工：feature 用 `jstack/spec-<spec 编号>`（spec 编号在 to-spec 发布后才有，这一步放到 to-spec 之后执行），bug-fix 用 `jstack/fix-<简短描述>`。

完成标准：当前不在默认分支上。

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
- 已经 PASS、可以关闭的 issue 编号
- 跳过的步骤和原因
```

## 示例

用户说："/jstack:j-mode 给订单列表加按状态筛选"

执行：选择 feature；用 brainstorm 追问两轮；用 to-spec 发布 spec #12，新建分支 `jstack/spec-12`；用 to-tickets 拆出 #13、#14；派 subagent 实现 #13，再执行 accept，结论为 PASS；#14 第一次 accept 判 FAIL，带上失败输出重新派一次 implement，第二次判 PASS。

结果：三段式汇报，"还有什么"里列出可以关闭的 #13、#14。

## 常见问题

现象：子 skill 的调用被 Harness 拒绝。
原因：jstack 的 skill 设置了只能手动调用。
处理：改为按 adapter 读取 `../<name>/SKILL.md` 并照做。

现象：同一张 ticket 第二次 accept 仍为 FAIL。
原因：ticket 切分有问题，或者验收检查本身写错了。
处理：停止后续 ticket，把两次 FAIL 的证据交给用户，由用户决定是修改 ticket 还是自己介入。
