---
name: accept
description: 当任务涉及独立验收一张 ticket 或一次修复是否完成时使用，由非作者 agent 执行。编写代码使用 implement。
disable-model-invocation: true
---

# 独立验收

> 骨架，待实现。

## 职责

非作者 agent 运行验收检查，给出 PASS / PASS+NOTES / FAIL；改动已有测试且未说明理由判 FAIL；需要驱动 app 时读取项目的 verify-<app>。
