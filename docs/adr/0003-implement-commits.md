# implement 完成后自动 commit

jstack 的 implement 做完之后，会直接把改动 commit 到当前分支，不再单独征求授权。这和用户全局 `AGENTS.md` 里"commit 需要明确授权"的规则相反。用户的考虑是：主动调用 implement 或 j-mode，本身就代表授权 commit；而且 j-mode 是按 ticket 串行派 subagent 执行的，每张 ticket 都要有一个独立的 commit，这样 accept 才能按 commit 做验收。push、PR 和部署不在这个授权范围内，仍然需要用户明确同意。
