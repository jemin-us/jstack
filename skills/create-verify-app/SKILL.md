---
name: create-verify-app
description: 当任务涉及为项目生成 verify-app 类 skill、让 agent 能像用户一样启动和操作 app 时使用。执行验收使用 accept。
disable-model-invocation: true
---

# 生成项目验证 skill

> 骨架，待实现。

## 职责

生成 Launch / Doctor / Drive / Evidence / Cleanup 五段；实体放 .agents/skills/verify-<app>/，symlink 到 .claude/skills/；生成后亲自跑一遍。
