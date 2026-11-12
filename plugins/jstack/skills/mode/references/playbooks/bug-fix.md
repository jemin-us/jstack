# Playbook：bug-fix

适用于现有行为出错、报错、性能退化。不写 spec，也不拆 ticket。

## 步骤

1. **建 worktree**：按 [worktree](../../../worktree/SKILL.md) 的"开始"一节新建 worktree 和新分支，基准是主目录的当前分支，新分支名用 `jstack/fix-<简短描述>`。之后每条命令都在这个 worktree 里执行。
   完成标准：worktree 绝对路径、新分支名、起点 commit 已记下。
2. **诊断并修复**：读取 [diagnosing-bugs](../../../diagnosing-bugs/SKILL.md) 并照做，包括修复和 commit。worktree 已在第 1 步建好，直接在其中工作。
   完成标准：拿到诊断结论（当前行为、期望行为、必须保持不变的行为），以及复现命令在修复前失败、修复后通过的两段输出。
3. **验收**：在 worktree 里读取 [accept](../../../accept/SKILL.md) 并照做。验收范围是"起点..新分支 HEAD"。验收检查有两部分：一是复现命令，二是"必须保持不变的行为"里能运行的那些检查。
   完成标准：拿到 accept 结论。
4. **处理 FAIL**：结论为 FAIL 时，带着失败详情回到 diagnosing-bugs 的修复步骤，再修一次，然后重新验收。第二次仍为 FAIL 就停止；失败详情写明"全部受阻"时不重试，直接停止。
   完成标准：结论为 PASS 或 PASS+NOTES，或者已按上面的条件停止。
5. **更新 issue**：bug 来自某个 issue 时，把 accept 结论评论到这个 issue 上；结论为 PASS 时关闭它，PASS+NOTES 时保持 open。没有对应 issue 时跳过。
6. **清理**：结论为 PASS 或 PASS+NOTES 时，按 [worktree](../../../worktree/SKILL.md) 的"清理"一节删除 worktree、保留分支。结论为 FAIL 时，保留 worktree 和分支。
   完成标准：worktree 已按结论删除或保留。
7. **收尾**：按 mode 第 4 步汇报，附上修复前失败、修复后通过的两段输出，告诉用户保留的分支名；worktree 被保留时，列出路径和 worktree skill "清理"一节的删除命令。
