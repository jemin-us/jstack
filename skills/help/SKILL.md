---
name: help
description: 当用户问 jstack 怎么用、有哪些 skill、某种情况该用哪个 skill 时使用。按用户的情况给出该用的 skill、调用的说法和之后的过程，只给建议，不执行。要直接开始开发使用 mode。
---

# jstack 使用帮助

## 流程

### 1. 弄清用户的情况

从用户的话里判断属于哪一种：想了解 jstack 整体怎么用，或者手上有一件具体的事，不知道交给哪个 skill。具体的事只有一句话看不出规模和类型时，问一次："这件事现在到哪一步了？只有想法、已经讨论清楚、已有 spec，还是已有 ticket？"

完成标准：已确定是整体介绍，还是某一件具体的事及其所处的阶段。

### 2. 对照地图选 skill

按下面的"地图"选出 skill。地图里的一句话只用来定位；向用户说明一个 skill 做什么、会在哪里停下来等用户之前，先读取它的 `SKILL.md`，按正文回答。

完成标准：选中的每个 skill 的 `SKILL.md` 都已读过。

### 3. 回复

整体介绍：讲"一句话跑完"和"只做一步"两种用法，各给一个调用的说法。

具体的事按以下三项回复：

- 用哪个 skill，以及一句选它的理由。
- 调用的说法，例如 `/jstack:mode 给订单列表加按状态筛选`。
- 之后的过程：它会依次做什么，在哪里停下来等用户，最后交付什么。

用户看完回复说"开始"时，读取选中的 skill 并照做。

完成标准：回复包含以上三项，或者用户已经得到整体介绍。

## 地图

### 第一次使用

在项目里先运行 [setup](../setup/SKILL.md)：检查 gh 环境和账号，生成项目的验证 skill。

### 一句话跑完

把请求交给 [mode](../mode/SKILL.md)，它判断规模和类型后依次执行其他 skill：

| 请求 | 过程 |
|---|---|
| 需要 spec 或要拆成多张 ticket 的功能 | brainstorm → `spec` → `tickets` → 并行 implement → 逐张 accept → 合并到集成分支 → pr |
| 一张 ticket 就能做完的改动 | implement → accept → pr |
| bug | diagnosing-bugs → accept → pr |

### 只做一步

| 情况 | skill |
|---|---|
| 想法还模糊，只想先讨论清楚 | [brainstorm](../brainstorm/SKILL.md) |
| 已讨论清楚，只要一份 spec | [spec](../spec/SKILL.md) |
| 已有 spec，只要拆成 ticket | [tickets](../tickets/SKILL.md) |
| 已有 ticket，或改动已经明确，只要实现 | [implement](../implement/SKILL.md) |
| 只要复现 bug、定位根因 | [diagnosing-bugs](../diagnosing-bugs/SKILL.md) |
| 已有分支或 commit，只要独立验收 | [accept](../accept/SKILL.md) |
| 分支已 commit，只要开 PR | [pr](../pr/SKILL.md) |

### 不属于开发流程

| 情况 | skill |
|---|---|
| 生成或更新项目的验证 skill | [create-verify-app](../create-verify-app/SKILL.md) |
| 固定项目的代码基准，把规则落成检查 | [codebase](../codebase/SKILL.md) |
| 审计一块代码的结构问题，只看不改 | [codebase-audit](../codebase-audit/SKILL.md) |
| 写或审查 `CLAUDE.md`、`AGENTS.md`、prompt 等给 agent 读的文字 | [prompt](../prompt/SKILL.md) |
| 新建、修改或审查 skill | [skill-creator-plus](../skill-creator-plus/SKILL.md) |

### 不由用户调用

[worktree](../worktree/SKILL.md)、[harness](../harness/SKILL.md)、[finish](../finish/SKILL.md) 只供其他 skill 读取。用户问到时说明这一点，不建议直接调用。

## 示例

用户说："我有个 bug，偶尔下单失败，该用哪个？"

执行：判断为具体的事，类型是 bug；地图指向 mode 和 diagnosing-bugs；读取两者的 `SKILL.md`。

回复：要修到开出 PR，用 `/jstack:mode 修复偶尔下单失败`，它会先让 diagnosing-bugs 拿到稳定失败的复现命令，修复后独立验收，再开 PR；只想知道原因，用 `/jstack:diagnosing-bugs`，它给出诊断结论后结束。

## 常见问题

现象：用户的事不在地图里，例如只想改一行文案。
原因：jstack 面向一张 ticket 大小及以上的改动。
处理：告诉用户这件事不需要 jstack，直接说出要改什么即可。
