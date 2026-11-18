# 收尾

仅 feature 和 bug-fix 执行本步。按 [harness](../../harness/SKILL.md) 的三段汇报，各段写：

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

仅当交付范围内的必需检查和独立审查通过时，汇报后读取 [pr](../../pr/SKILL.md) 并照做，分支在 feature 下是集成分支，在 bug-fix 下是修复分支，正文用上面的三段汇报。CI 修复继续使用原 worktree，累计审查轮数不重置。仅当 pr 核实当前 HEAD 为 READY（或已核实 MERGED），才关闭已完成的 issue，并按 [worktree](../../worktree/SKILL.md) 清理对应的集成或修复 worktree、保留分支；失败或受阻时保留。

完成标准：PR 和对应 HEAD 的 CI 结果已告诉用户；失败、受阻或明确限定范围时保留现场并说明未交付项，不以创建 PR 代替 CI 通过。feature 仅在交付成功后清理集成 worktree。
