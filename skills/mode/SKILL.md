---
name: mode
description: 当用户提出泛化的开发请求时使用，例如“加个功能”“给订单列表加按状态筛选”“改一下这个行为”“修这个 bug”。按 jstack 工作流判断规模和类型：需要 spec 或要拆成多张 ticket 的功能走 feature playbook，bug 走 bug-fix playbook，一个 ticket 就能做完的小改动（例如“给脚本加个参数”）交给 implement，依次执行其他 jstack skill 完整推进。请求已指明 ticket 编号、spec 编号或待验收的分支时，使用对应的 implement、to-tickets、accept。
---

# jstack 入口

## 硬性规则

- 先读取 [harness](../harness/SKILL.md)，整个会话只读一次。下文的"读取 skill""派 subagent""向用户提问"和 `<jstack 插件目录>` 都按它执行。
- mode 发起的流程是自动执行：本 skill 读取的 skill，以及它们再读取的 skill，凡写着"自动执行时"的分支都适用。
- 回复中的每个论断都要标明证据等级：已运行、推断、未验证。自己能跑的检查不交给用户。
- 写入 GitHub（push、开 PR、创建或修改 issue）前，按 [setup](../setup/SKILL.md) 的"写入 GitHub 前检查账号"一节确认当前 gh 账号有写权限。
- issue 状态只由 mode 修改，规则和命令见 [references/issue-state.md](references/issue-state.md)。
- 验收结论只来自 accept，作者不能给自己出结论。

## 流程

### 1. 选 playbook

根据用户请求，从下表中选一个：

| playbook | 适用 | 执行方式 |
|---|---|---|
| feature | 需要拆成多张 ticket 或需要 spec 的新功能、行为变更 | [feature.md](references/playbooks/feature.md) |
| change | 一个 ticket 就能做完、不需要 spec 的改动 | 读取 [implement](../implement/SKILL.md) 并照做，不创建 issue |
| bug-fix | 现有行为出错、报错、性能退化 | [bug-fix.md](references/playbooks/bug-fix.md) |

完成标准：向用户说明选了哪个 playbook，并给出一句理由。选 change 时，向用户说明这次交给 implement，最终汇报里也写明由 implement 完成；implement 自己建 worktree、实现、accept 和清理，读取它的 `SKILL.md` 并照做后不再执行下面的步骤。都不适用时，说明改用哪个 jstack skill，然后直接读取它的 `SKILL.md` 并照做，不再执行下面的步骤。

### 2. 准备分支

只有 feature 执行本步，并且放到 to-spec 发布之后，因为分支名要用 spec 编号：按 [worktree](../worktree/SKILL.md) 的"集成 worktree"一节新建集成 worktree 和集成分支 `jstack/spec-<spec 编号>`，各 ticket 的改动最后都合并到这里。

完成标准：feature 的集成 worktree 已建好，绝对路径已记下；bug-fix 和 change 已标为跳过。

### 3. 执行 playbook

读取选定的 playbook 文件，把它的步骤原样抄进任务列表，按步骤执行，每完成一步就勾掉。不做的步骤保留在列表里，标为"跳过：<原因>"。feature playbook 派 subagent 实现 ticket 时，brief 用 [references/implement-brief.md](references/implement-brief.md)。

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
- 按推荐答案定的假设、subagent 做出的假设、选定的测试接缝
- 仍为 open 的 issue 及其状态（验收失败 / 待人工验收）
- 跳过的步骤和原因
```

汇报后读取 [pr](../pr/SKILL.md) 并照做，分支在 feature 下是集成分支，在 bug-fix 下是修复分支，正文用上面的三段汇报。之后，feature 按 [worktree](../worktree/SKILL.md) "清理"一节删除集成 worktree、保留集成分支，并告诉用户分支名。

完成标准：PR 已创建，链接已告诉用户；feature 的集成 worktree 已删除。

## 示例

用户说："/jstack:mode 给订单列表加按状态筛选"

执行：选择 feature；brainstorm 只问一个问题"筛选条件要不要保留在 URL 里"，其余决定按推荐答案记为假设；用 to-spec 发布 spec #12，在集成 worktree 里新建分支 `jstack/spec-12`；用 to-tickets 拆出互不阻塞的 #13、#14；两张在各自的 worktree 里并行实现；#13 验收 PASS 后合并；#14 第一次 accept 判 FAIL，带上失败输出重新派一次 subagent，第二次判 PASS 后合并；集成分支全量测试通过。

结果：#13、#14 评论了验收结论并关闭，#12 随之关闭；按三段式汇报，列出记为假设的决定；开出 `jstack/spec-12` 到默认分支的 PR，删除集成 worktree。

## 常见问题

现象：同一张 ticket 第二次 accept 仍为 FAIL。
原因：ticket 切分有问题，或者验收检查本身写错了。
处理：停止后续 ticket，把两次 FAIL 的证据交给用户，由用户决定是修改 ticket 还是自己介入。
