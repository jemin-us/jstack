# Playbook：feature

适用于新功能和行为变更。前三步需要和用户交互，在主会话里完成。之后每张 ticket 由 subagent 实现，主会话负责调度和验收。

## 步骤

1. **追问需求**：读取 [brainstorm](../../../brainstorm/SKILL.md) 并照做。
   完成标准：用户确认理解一致，没有待定问题。用户一开始就给出清楚的需求时，标为"跳过：需求已明确"。
2. **写 spec**：读取 [to-spec](../../../to-spec/SKILL.md) 并照做。
   完成标准：spec issue 已发布，记下编号。之后按 j-mode 第 2 步新建分支。
3. **拆 ticket**：读取 [to-tickets](../../../to-tickets/SKILL.md) 并照做。
   完成标准：ticket 已发布，并带有子 issue 关系和阻塞关系。
4. **逐张实现和验收**：按阻塞关系的顺序，一次只处理一张 ticket，不并行。所有阻塞它的 ticket 都已 PASS 的，才能开始。对每张 ticket：
   1. 记下 `git rev-parse HEAD`，作为验收范围的起点。
   2. 按 [implement-brief.md](../implement-brief.md) 填好 brief，派 subagent 执行。
   3. subagent 汇报验收检查没通过、没有 commit 时，跳过本步，直接按 4.4 重试。否则读取 [accept](../../../accept/SKILL.md) 并照做，验收范围是"起点..HEAD"，验收检查来自这张 ticket。
   4. 结论为 FAIL 时，把失败详情附在 brief 末尾，重新派一次 subagent。第二次仍为 FAIL，就停止整个 playbook，进入收尾。
   5. 结论为 PASS 或 PASS+NOTES 时，记下结论和受阻项，处理下一张。
   完成标准：每张 ticket 都有 accept 结论。
5. **收尾**：按 j-mode 第 4 步汇报。

## 注意

- subagent 无法向用户提问。遇到歧义时，它会按最保守的理解继续，并把假设写进汇报。主会话把这些假设带进收尾，不在中途打断用户。
