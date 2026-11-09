---
name: accept
description: 当任务涉及独立验收一张 ticket、一次 bug 修复或一段 commit 是否真正完成时使用，由非作者 agent 运行验收检查并给出 PASS、PASS+NOTES 或 FAIL。编写代码使用 implement，定位 bug 使用 diagnosing-bugs。
disable-model-invocation: true
---

# 独立验收

## 硬性规则

- 验收结论只能由没写这段代码的 agent 给出。作者只知道自己想做成什么，不知道实际做成了什么。
- 每条结论都来自实际运行。没跑过的检查不算通过；结果无法判定也不算通过。
- 每条 FAIL 都要附能复跑的命令和实际输出。风格、命名、"以后可能出问题"这类意见不算问题。
- 改动已有测试却没有说明理由，直接判 FAIL。
- 验收只报告，不修代码。

## 流程

### 1. 收集输入

需要三样东西：

1. **验收范围**：commit 范围（如 `<base>..HEAD`），或调用者明确给出的 diff。j-mode 调用时会传入；用户直接调用时，默认取当前分支相对仓库默认分支的范围（默认分支用 `git symbolic-ref --short refs/remotes/origin/HEAD` 查出），并向用户确认。
2. **验收检查**：
   - 有 ticket 时，运行 `gh issue view <编号> --json title,body` 读取 `## 验收检查` 一节。
   - bug-fix 场景：取 diagnosing-bugs 产出的复现命令，以及"必须保持不变的行为"。
   - 用户直接给出的检查，原样使用。
3. **启动和操作方式**：查找项目里的 `verify-<app>` skill，位置是 `.agents/skills/verify-*/` 或 `.claude/skills/verify-*/`。有就把它的 `SKILL.md` 路径带上；没有就跳过。

完成标准：手上有确定的验收范围，以及至少一条验收检查。一条都没有时，停下来向用户要，不自己编。

### 2. 派 subagent 执行 brief

按 [references/brief.md](references/brief.md) 填好 brief，派一个 subagent 执行。subagent 怎么派，按当前 Harness 的 adapter 来：[Claude Code](../j-mode/references/harness/claude-code.md)、[Codex](../j-mode/references/harness/codex.md)。

关键：brief 里只放验收范围、验收检查和 `verify-<app>` 路径。不放作者的思路、实现说明和自评，以免验收者沿着作者的假设去验证。

完成标准：subagent 返回了逐条检查的结果表，以及测试改动检查的结果。

### 3. 核对 subagent 的结果

不要只看 subagent 的总结，自己做三件事：

1. 复跑每条 FAIL 的命令，确认失败可以复现。复现不了的，降为 NOTES，并写明原因。
2. 对照 diff，确认每条 PASS 的命令确实覆盖了 ticket 描述的行为，而不是测了一条无关的路径。
3. 自己跑 `git diff --name-status <范围>`，确认测试改动检查没有漏项。

完成标准：每条结论都经主 agent 核对过。

### 4. 给出结论

| 结论 | 条件 |
|---|---|
| PASS | 所有验收检查通过，没有未说明理由的测试改动 |
| PASS+NOTES | 所有验收检查通过，但有值得用户知道的发现，比如有检查项受阻、或者有复现不了的异常 |
| FAIL | 任一验收检查不通过；改动已有测试却没说明理由；在错误的使用面上验证；结果无法判定 |

受阻的检查（需要联网或浏览器，但环境做不到）单独列出，标"受阻"。只要有受阻项，结论最多是 PASS+NOTES。

按下面的格式回复：

```markdown
## 结论：PASS | PASS+NOTES | FAIL

验收范围：<base>..<head>

| # | 验收检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | `<命令>` → <期望> | 通过 / 失败 / 受阻 | <实际输出摘录> |

测试改动：无 / <文件> 已说明理由 / <文件> 未说明理由

失败详情（仅 FAIL）：每条写复跑命令、实际输出、期望输出。
```

## 示例

**示例 1：j-mode 验收一张 ticket**

j-mode 传入 ticket #42 和范围 `a1b2c3..d4e5f6`。读出两条验收检查，派 subagent 执行。subagent 报告第 1 条通过，第 2 条 `curl localhost:3000/api/orders?status=paid` 返回 500。主 agent 复跑后同样得到 500。结论为 FAIL，附上命令和响应体，交回 j-mode。

**示例 2：用户验收一次 bug 修复**

用户说"验收一下刚才的修复"。取当前分支相对 `main` 的范围，向用户确认。验收检查是 diagnosing-bugs 给出的复现命令 `pnpm test src/cart.test.ts -t "空购物车"`，加上一条保持不变的行为"非空购物车结算金额不变"。两条都通过，但 diff 修改了 `src/cart.test.ts` 里一条已有断言，commit 信息里也没说明理由。结论为 FAIL。

## 常见问题

现象：subagent 报告"全部通过"，但没有贴出任何输出。
原因：subagent 写的是总结，没有逐条实际运行。
处理：退回给 subagent，要求按 brief 的表格逐条贴出命令和实际输出。仍然拿不到时，主 agent 自己运行。

现象：验收检查依赖一个本地没在运行的服务。
原因：项目没有 `verify-<app>`，或者服务没启动。
处理：有 `verify-<app>` 就按它的启动步骤运行；没有就把该条标为"受阻"，并在结论里建议运行 jstack skill create-verify-app。

现象：找不到 ticket 里的 `## 验收检查` 一节。
原因：ticket 不是 to-tickets 生成的，或者被手动改过。
处理：向用户要验收检查，不要从 ticket 正文里猜。
