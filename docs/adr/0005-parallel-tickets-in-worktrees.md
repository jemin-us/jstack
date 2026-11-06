# ticket 按波次并行实现，每张 ticket 一个 worktree

feature playbook 把阻塞项都已完成的 ticket 编成一个波次，一波最多 3 张，并行实现。每张 ticket 在 j-mode 用 `git worktree add` 建的独立 worktree 和分支里开发，验收通过后再合并回集成分支 `jstack/spec-<编号>`。每一波结束时，在集成分支上跑一次全量测试。最初定的是串行，后来改成并行，因为用户希望提高效率。worktree 由 j-mode 自己创建，不依赖 Harness 自带的隔离：Claude 的 Agent 工具支持 worktree 隔离，但没有查到 Codex 的 worker 有对应的能力。

## Consequences

- 合并冲突时，在原 worktree 里重新派一次 subagent，让它 rebase 到集成分支后解决冲突；仍然冲突就按 FAIL 处理。
- to-tickets 需要让没有阻塞关系的 ticket 改动不同的模块，以减少冲突。
- 一张 ticket 最终 FAIL 时，只停掉依赖它的 ticket。
