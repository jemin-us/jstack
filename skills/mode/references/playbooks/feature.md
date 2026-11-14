# Playbook：feature

适用于新功能和行为变更。前三步在主会话里完成，只有第 1 步可能向用户提问。之后的 ticket 按波次并行实现，主会话负责调度、验收和合并。

## 步骤

1. **追问需求**：读取 [brainstorm](../../../brainstorm/SKILL.md) 并照做。
   完成标准：每个决定要么用户已回答，要么按推荐答案记为假设。
2. **写 spec**：读取 [spec](../../../spec/SKILL.md) 并照做。
   完成标准：spec issue 已发布，记下编号。之后按 mode 第 2 步新建集成 worktree 和集成分支 `jstack/spec-<编号>`。
3. **拆 ticket**：读取 [tickets](../../../tickets/SKILL.md) 并照做。
   需求附带截图或设计稿时，按 [visual.md](visual.md) 第 1 步把它转成验收条目，写进对应 ticket 的验收检查。
   完成标准：ticket 已发布，并带有子 issue 关系和阻塞关系。
4. **按波次实现和验收**：重复以下过程，直到没有可以开工的 ticket。
   1. **算出本波**：阻塞项都已合并到集成分支、且本次尚未验收并合并的 open ticket，构成本波。维护已合并 ticket 与 commit 的记录：等待 CI 而保持 open 的已合并项不再派发，其依赖视为已满足；BLOCKED 的 ticket 不算完成，不合并。一波最多 3 张，多出的留到下一波。阻塞项用 [issue-state.md](../issue-state.md) 里的命令查。
   2. **定基准和分支**：每张 ticket 的基准是集成分支 `jstack/spec-<spec 编号>`，新分支名是 `jstack/spec-<spec 编号>-t<编号>`。mode 不自己建 worktree，由 implement 按 [worktree](../../../worktree/SKILL.md) 建好后回报路径、分支和起点。把 ticket 指派给当前账号。
   3. **并行实现**：按 mode 第 3 步给出的 implement-brief.md 为每张 ticket 填好 brief，然后同时派出 subagent。
   4. **逐张验收**：每个 subagent 返回后，记下它回报的 worktree 路径、分支和起点 commit。在这个 worktree 里（每条命令都以 `cd <worktree 绝对路径> &&` 开头）读取 [accept](../../../accept/SKILL.md) 并照做，验收范围是"起点..ticket 分支 HEAD"。subagent 汇报验收检查没通过、没有 commit 的，跳过验收，直接按第 6 小步重试。
   5. **合并**：PASS 或 PASS+NOTES 的 ticket，在集成 worktree 里运行 `git merge --no-ff <ticket 分支>`（命令以 `cd <集成 worktree 绝对路径> &&` 开头）。有冲突时先 `git merge --abort`，再按第 6 小步重试，brief 末尾附上冲突的文件。合并成功后，按 [issue-state.md](../issue-state.md) 评论结论并保持 ticket open，待集成分支 pr 核实当前 HEAD 为 READY（或已核实 MERGED）后再关闭，然后按 [worktree](../../../worktree/SKILL.md) 的"清理"一节删除 worktree 和 ticket 分支。
   6. **重试**：验收 FAIL 或合并冲突时，在原 worktree 里重新派 subagent，brief 里写明已有 worktree 的路径和起点，末尾附上失败详情，然后重新验收、合并。累计三轮审查仍失败，或环境问题无法解决而 BLOCKED（不盲目重试），就把结论评论到 ticket 上，保持 open，并保留 worktree 和分支供用户排查。依赖这张 ticket 的 ticket 不再开工，其余照常进行。
   7. **波次收尾**：本波全部处理完后，在集成 worktree 里运行一次全量测试。失败时停止整个 playbook，进入收尾。
   完成标准：每张 ticket 都有 accept 结论，并已评论到 issue 上；集成分支的全量测试通过。关闭 ticket 和 spec 统一按 mode 的收尾规则执行，不在波次内提前关闭。
5. **收尾**：按 mode 第 4 步汇报，另外列出因上游失败而没有开工的 ticket，以及保留下来的 worktree 路径和 worktree skill "清理"一节的删除命令。push、开 PR 和删除集成 worktree 按 mode 第 4 步执行。

## 注意

- subagent 汇报里写的假设，主会话带进收尾，不在中途打断用户。
