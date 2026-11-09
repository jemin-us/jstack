# Playbook：feature

适用于新功能和行为变更。前三步需要和用户交互，在主会话里完成。之后的 ticket 按波次并行实现，主会话负责调度、验收和合并。

## 步骤

1. **追问需求**：读取 [brainstorm](../../../brainstorm/SKILL.md) 并照做。
   完成标准：用户确认理解一致，没有待定问题。用户一开始就给出清楚的需求时，标为"跳过：需求已明确"。
2. **写 spec**：读取 [to-spec](../../../to-spec/SKILL.md) 并照做。
   完成标准：spec issue 已发布，记下编号。之后按 j-mode 第 2 步新建集成 worktree 和集成分支 `jstack/spec-<编号>`。
3. **拆 ticket**：读取 [to-tickets](../../../to-tickets/SKILL.md) 并照做。
   完成标准：ticket 已发布，并带有子 issue 关系和阻塞关系。
4. **按波次实现和验收**：重复以下过程，直到没有可以开工的 ticket。
   1. **算出本波**：阻塞项都已合并到集成分支的 open ticket，构成本波；因受阻而保持 open、但已经合并的 ticket，算作已完成。一波最多 3 张，多出的留到下一波。阻塞项用 [issue-state.md](../issue-state.md) 里的命令查。
   2. **定基准和分支**：每张 ticket 的基准是集成分支 `jstack/spec-<spec 编号>`，新分支名是 `jstack/spec-<spec 编号>-t<编号>`。j-mode 不自己建 worktree，由 implement 按 [worktree.md](../../../implement/references/worktree.md) 建好后回报路径、分支和起点。把 ticket 指派给当前账号。
   3. **并行实现**：按 [implement-brief.md](../implement-brief.md) 为每张 ticket 填好 brief，然后同时派出 subagent。
   4. **逐张验收**：每个 subagent 返回后，记下它回报的 worktree 路径、分支和起点 commit。在这个 worktree 里（每条命令都以 `cd <worktree 绝对路径> &&` 开头）读取 [accept](../../../accept/SKILL.md) 并照做，验收范围是"起点..ticket 分支 HEAD"。subagent 汇报验收检查没通过、没有 commit 的，跳过验收，直接按第 6 小步重试。
   5. **合并**：PASS 或 PASS+NOTES 的 ticket，在集成 worktree 里运行 `git merge --no-ff <ticket 分支>`（命令以 `cd <集成 worktree 绝对路径> &&` 开头）。有冲突时先 `git merge --abort`，再按第 6 小步重试，brief 末尾附上冲突的文件。合并成功后，按 [issue-state.md](../issue-state.md) 评论结论并关闭 ticket（PASS+NOTES 有受阻项时保持 open），然后按 [worktree.md](../../../implement/references/worktree.md) 的"清理"一节删除 worktree 和 ticket 分支。
   6. **重试**：验收 FAIL 或合并冲突时，在原 worktree 里重新派一次 subagent，brief 里写明已有 worktree 的路径和起点，末尾附上失败详情，然后重新验收、合并。第二次仍失败，就把结论评论到 ticket 上，保持 open，并保留 worktree 和分支供用户排查。依赖这张 ticket 的 ticket 不再开工，其余照常进行。
   7. **波次收尾**：本波全部处理完后，在集成 worktree 里运行一次全量测试。失败时停止整个 playbook，进入收尾。
   完成标准：每张 ticket 都有 accept 结论，并已评论到 issue 上；集成分支的全量测试通过。spec 下的 ticket 全部关闭时，关闭 spec。
5. **收尾**：按 j-mode 第 4 步汇报，另外列出因上游失败而没有开工的 ticket，以及保留下来的 worktree 路径和 worktree.md 里的删除命令。push、开 PR 和删除集成 worktree 按 j-mode 第 4 步执行。

## 注意

- subagent 无法向用户提问。遇到歧义时，它会按最保守的理解继续，并把假设写进汇报。主会话把这些假设带进收尾，不在中途打断用户。
- 每个 subagent 只能改动自己的 worktree，不能切换主目录的分支，也不能碰集成分支和集成 worktree。
