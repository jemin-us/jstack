# implement 和 diagnosing-bugs 完成后自动 commit

jstack 的 implement 做完之后，会直接把改动 commit 到它在项目内 worktree 里新建的分支上。diagnosing-bugs 修复后也一样，它负责复现、修复和 commit，bug-fix playbook 不再单独调用 implement。两者都不再单独征求授权。这和用户全局 `AGENTS.md` 里"commit 需要明确授权"的规则相反。前提是：skill 改为自动调用后，用户不一定主动调用过 implement 或 j-mode，所以 commit 只落在 worktree 的新分支上，不碰用户当前的分支和目录，默认分支上也不会多出 commit。worktree 规则见 `skills/implement/references/worktree.md`。另外，j-mode 按 ticket 派 subagent 执行，每张 ticket 都要有自己的 commit，accept 才能按 commit 范围做验收。push、PR 和部署不在这个授权范围内，仍然需要用户明确同意。
