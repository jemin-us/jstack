---
name: finish
description: 对已 commit 的 worktree 分支执行 accept，按结论清理 worktree，汇报后读取 pr。implement、diagnosing-bugs 单独使用时在 commit 后读取，不单独使用。
disable-model-invocation: true
---

# 收尾

调用方传入五项：worktree 绝对路径、新分支名、起点 commit、验收检查、写好的三段汇报。

## 流程

### 1. 验收

读取 [accept](../accept/SKILL.md) 并照做，不提示用户手动调用。验收范围是"起点..新分支 HEAD"，验收检查用调用方传入的，每条命令都在 worktree 里执行。

完成标准：拿到 accept 结论。

### 2. 清理

| accept 结论 | worktree | 分支 |
|---|---|---|
| PASS 或 PASS+NOTES | 按 [worktree](../worktree/SKILL.md) 的"清理"一节删除 | 保留 |
| FAIL | 保留 | 保留 |

完成标准：worktree 已按上表删除或保留。

### 3. 汇报

在调用方的三段汇报里补上三项，然后发给用户：

- "改了什么"：worktree 已删除或保留，以及分支名；保留时列出 worktree 路径。
- "验证了什么"：accept 结论和关键证据（已运行）。
- "还有什么"：accept 标为"受阻"的检查。

完成标准：用户收到的汇报包含 accept 结论和分支名。

### 4. 开 PR

结论为 PASS 或 PASS+NOTES 时，读取 [pr](../pr/SKILL.md) 并照做，分支是新分支，正文用上一步的汇报。结论为 FAIL 时不开 PR，到上一步结束。

完成标准：pr 的流程已走完，或因 FAIL 没有执行。

## 示例

implement 单独实现 #42 后传入：worktree `.claude/worktrees/jstack-health-check`、分支 `jstack/health-check`、起点 `a1b2c3`、验收检查 `curl -s localhost:3000/health` → `OK`。accept 结论为 PASS；删除 worktree、保留分支；汇报里补上"accept 结论 PASS""分支 `jstack/health-check` 已保留"；读取 pr，用户同意后开出 PR。

结果：用户拿到带 accept 结论的汇报和 PR 链接。

## 常见问题

现象：accept 结论为 FAIL。
原因：验收检查没通过、全部受阻，或改动了已有测试却没说明理由。
处理：不自行修改代码重试。汇报里列出失败的检查和证据、worktree 路径和分支名，由用户决定下一步。
