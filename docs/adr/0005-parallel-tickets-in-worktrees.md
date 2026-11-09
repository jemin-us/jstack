# ticket 按波次并行实现，每张 ticket 一个 worktree

feature playbook 把阻塞项都已完成的 ticket 编成一个波次，一波最多 3 张，并行实现。每张 ticket 在独立的 worktree 和分支里开发，worktree 由 implement 按 `skills/implement/references/worktree.md` 在项目内创建（Claude Code 用 `.claude/worktrees/`，Codex 用 `.codex/worktrees/`），j-mode 只传入集成分支作为基准，验收通过后再合并回集成分支 `jstack/spec-<编号>`。每一波结束时，在集成分支上跑一次全量测试。最初定的是串行，后来改成并行，因为用户希望提高效率。worktree 用 git 命令自建，不依赖 Harness 自带的功能：Codex 自带的 worktree 只能放在用户级全局目录，Claude Code 自带的不能指定分支名和起点。

## Consequences

- 合并冲突时，在原 worktree 里重新派一次 subagent，让它 rebase 到集成分支后解决冲突；仍然冲突就按 FAIL 处理。
- to-tickets 需要让没有阻塞关系的 ticket 改动不同的模块，以减少冲突。
- 一张 ticket 最终 FAIL 时，只停掉依赖它的 ticket。
- ticket 合并后，j-mode 删除它的 worktree 和分支；两次验收仍失败的保留，并在收尾列出路径和删除命令。
