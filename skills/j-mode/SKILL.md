---
name: j-mode
description: 当任务需要按 jstack 工作流完整推进时使用，包括新功能（feature）和修 bug（bug-fix）。选中 playbook 后按步骤调用其他 jstack skill。只问 jstack 某个 skill 怎么用时，直接读该 skill。
disable-model-invocation: true
---

# jstack 入口

> 骨架，待实现。

## 职责

选 playbook，按路径读取并执行子 skill；回复标明证据等级（已运行/推断/未验证）；按"改了什么 / 验证了什么 / 还有什么"收尾。

## Harness 适配

开始前按当前 Harness 读取一次对应 adapter：[Claude Code](references/harness/claude-code.md)、[Codex](references/harness/codex.md)。
