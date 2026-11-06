# Playbook：bug-fix

适用于现有行为出错、报错、性能退化。不写 spec，也不拆 ticket。修复由 diagnosing-bugs 完成，验收由 accept 完成。

## 步骤

1. **记下起点**：运行 `git rev-parse HEAD`，作为验收范围的起点。
   完成标准：起点 commit 已记下。
2. **诊断并修复**：读取 [diagnosing-bugs](../../../diagnosing-bugs/SKILL.md) 并照做，包括修复和 commit。
   完成标准：拿到诊断结论（当前行为、期望行为、必须保持不变的行为），以及复现命令在修复前失败、修复后通过的两段输出。
3. **验收**：读取 [accept](../../../accept/SKILL.md) 并照做。验收范围是"起点..HEAD"。验收检查有两部分：一是复现命令，二是"必须保持不变的行为"里能运行的那些检查。
   完成标准：拿到 accept 结论。
4. **处理 FAIL**：结论为 FAIL 时，带着失败详情回到 diagnosing-bugs 的修复步骤，再修一次，然后重新验收。第二次仍为 FAIL 就停止。
   完成标准：结论为 PASS 或 PASS+NOTES，或者两次 FAIL 后停止。
5. **收尾**：按 j-mode 第 4 步汇报，并附上修复前失败、修复后通过的两段输出。
