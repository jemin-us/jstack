---
name: mode
description: 当用户提出泛化的开发请求时使用，例如“加个功能”“给订单列表加按状态筛选”“改一下这个行为”“修这个 bug”。按 jstack 工作流判断规模和类型：需要 spec 或要拆成多张 ticket 的功能走 feature playbook，bug 走 bug-fix playbook，一个 ticket 就能做完的小改动交给 implement；代码清理、定期重构和基线维护走 maintenance playbook，依次执行其他 jstack skill 完整推进。请求已指明 ticket 编号、spec 编号或待验收的分支时，使用对应的 implement、`tickets`、accept。
---

# jstack 入口

## 硬性规则

- 先读取 [harness](../harness/SKILL.md)，整个会话只读一次。下文的"读取 skill""派 subagent""向用户提问"和 `<jstack 插件目录>` 都按它执行。
- 开发任务默认做到实现、验证、独立审查、commit、push、PR 和 CI 跟进，不逐步请求继续。合并、发布和不可恢复的数据删除不在默认范围；明确的仅分析、仅本地或禁止提交要求优先。读取技能用于评估不代表已经执行；开始时说明所选路径和交付终点，偏离时说明具体步骤与原因。
- mode 发起的流程是自动执行：本 skill 读取的 skill，以及它们再读取的 skill，凡写着"自动执行时"的分支都适用。
- 回复中的每个论断都要标明证据等级：已运行、推断、未验证。自己能跑的检查不交给用户。
- 写入 GitHub（push、开 PR、创建或修改 issue）前，按 [setup](../setup/SKILL.md) 的"写入 GitHub 前检查账号"一节确认当前 gh 账号有写权限。
- issue 状态只由 mode 修改，规则和命令见 [references/issue-state.md](references/issue-state.md)。
- 验收结论只来自 accept，作者不能给自己出结论。

## 流程

### 1. 选 playbook

用户要求暂停、恢复或交接时先读取 [session](../session/SKILL.md)，不重启整个开发流程。跨模块契约和领域建模由 implement 调用 [architect](../architect/SKILL.md)。用户要求技能行为评测时读取 [evaluate](../evaluate/SKILL.md)。

根据用户请求，从下表中选一个：

| playbook | 适用 | 执行方式 |
|---|---|---|
| feature | 需要拆成多张 ticket 或需要 spec 的新功能、行为变更 | [feature.md](references/playbooks/feature.md) |
| change | 一个 ticket 就能做完、不需要 spec 的改动 | 读取 [implement](../implement/SKILL.md) 并照做，不创建 issue |
| bug-fix | 现有行为出错、报错、性能退化 | [bug-fix.md](references/playbooks/bug-fix.md) |
| maintenance | 清理冗余、定期重构、减少代码基线中的已有违规 | [maintenance.md](references/playbooks/maintenance.md) |
| perf | 有测量依据的性能退化或明确性能目标 | [perf.md](references/playbooks/perf.md) |
| visual | 按设计、截图或参照调整视觉与交互，包括同一任务内追加的样式反馈 | [visual.md](references/playbooks/visual.md) |

完成标准：向用户说明选了哪个 playbook，并给出一句理由。选 change 时，向用户说明这次交给 implement，最终汇报里也写明由 implement 完成；implement 自己建 worktree、实现，再由 finish 执行 accept、修复闭环、PR 和清理，读取它的 `SKILL.md` 并照做后不再执行下面的步骤。maintenance、perf、visual 按对应 playbook 完成后结束，不重复执行通用收尾。只读调查和服务操作不进入开发交付流程；选用适合的只读技能或直接操作并验证，不为这些任务创建开发 PR。

### 2. 准备分支

只有 feature 执行本步，并且放到 `spec` 发布之后，因为分支名要用 spec 编号：按 [worktree](../worktree/SKILL.md) 的"集成 worktree"一节新建集成 worktree 和集成分支 `jstack/spec-<spec 编号>`，各 ticket 的改动最后都合并到这里。

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
- 每张 ticket 的 accept 结论（PASS / PASS+NOTES / BLOCKED / FAIL）和关键证据（已运行）

**还有什么**
- 受阻的验收检查，以及原因
- 当前 HEAD 未验证的检查；用户确认结束不代替技术验收
- 按推荐答案定的假设、subagent 做出的假设、选定的测试接缝
- 仍为 open 的 issue 及其状态（验收失败 / 验收受阻 / 待交付验证）
- 跳过的步骤和原因
```

仅当交付范围内的必需检查和独立审查通过时，汇报后读取 [pr](../pr/SKILL.md) 并照做，分支在 feature 下是集成分支，在 bug-fix 下是修复分支，正文用上面的三段汇报。CI 修复继续使用原 worktree，累计审查轮数不重置。仅当 pr 核实当前 HEAD 为 READY（或已核实 MERGED），才关闭已完成的 issue，并按 [worktree](../worktree/SKILL.md) 清理对应的集成或修复 worktree、保留分支；失败或受阻时保留。

完成标准：PR 和对应 HEAD 的 CI 结果已告诉用户；失败、受阻或明确限定范围时保留现场并说明未交付项，不以创建 PR 代替 CI 通过。feature 仅在交付成功后清理集成 worktree。

## 示例

用户说："/jstack:mode 给订单列表加按状态筛选"

执行：选择 feature；brainstorm 只问一个问题"筛选条件要不要保留在 URL 里"，其余决定按推荐答案记为假设；用 `spec` 发布 spec #12，在集成 worktree 里新建分支 `jstack/spec-12`；用 `tickets` 拆出互不阻塞的 #13、#14；两张在各自的 worktree 里并行实现；#13 验收 PASS 后合并；#14 第一次 accept 判 FAIL，带上失败输出重新派一次 subagent，第二次判 PASS 后合并；集成分支全量测试通过。

结果：#13、#14 评论验收结论；开出集成分支 PR，核实 pr 对当前 HEAD 返回 READY 后关闭 #13、#14 和 #12，清理集成 worktree；汇报 PR、验证结果和所作假设。

## 常见问题

现象：同一张 ticket 第三轮 accept 仍为 FAIL。
原因：ticket 切分有问题，或者验收检查本身写错了。
处理：停止后续 ticket，把三轮 FAIL 的证据交给用户，由用户决定是修改 ticket 还是自己介入。
