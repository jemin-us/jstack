---
name: pr
description: 当用户要求 push 分支并开 PR、发 PR、提 pull request 时使用；mode、finish 收尾时也读取它。只 push 已 commit 的分支并创建 PR，不 commit、不合并。写代码使用 implement；验收使用 accept。
---

# push 并开 PR

## 硬性规则

- 只 push 已经 commit 的内容。commit 由 implement 或 diagnosing-bugs 完成。
- 不使用 `--force`。

## 流程

以下命令都以 `cd <主目录> &&` 开头，`<主目录>` 是 `git rev-parse --show-toplevel` 在用户当前目录的结果。

### 1. 确定分支

- `<分支>`：调用方给的分支；没给时用 `git branch --show-current`。
- `<默认分支>`：`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`。
- 运行 `git log --oneline <默认分支>..<分支>`。

完成标准：`<分支>` 不是 `<默认分支>`，且上面的命令至少列出一个 commit。`<分支>` 就是默认分支，或者没有 commit 时，停下告诉用户原因。

### 2. 核对交付范围

开发流程进入本 skill 时默认自动 push 并开 PR，不逐步询问。用户明确限定仅本地修改或禁止外发时，到该范围结束并保留成果。合并、发布不属于本 skill。

完成标准：分支和交付终点与用户要求一致。

### 3. 检查账号并 push

1. 按 [setup](../setup/SKILL.md) 的"写入 GitHub 前检查账号"一节确认当前 gh 账号有写权限。
2. 运行 `git push -u origin <分支>`。

完成标准：push 成功，`git status -sb` 显示分支与远端同步。

### 4. 开 PR

1. 运行 `gh pr list --head <分支> --json url --jq '.[].url'`。有输出说明 PR 已存在，核实目标分支，更新其标题和正文以反映当前改动，不创建重复 PR。
2. 准备标题和正文：调用方给了收尾汇报时，正文用它；用户直接要求时，根据 `git log <默认分支>..<分支>` 写"改了什么、验证了什么、还有什么"三段，没跑过的检查标"未验证"。标题用一句话概括这些 commit。
3. 新 PR 用下面的创建命令；已有 PR 用 `gh pr edit` 更新，正文均使用文件参数。正文包含改动、验证和回滚方式，不把聊天过程写进去。正文写进 `f=$(mktemp)`，运行：

   ```bash
   gh pr create --base <默认分支> --head <分支> --title "<标题>" --body-file "$f"
   ```

完成标准：拿到 PR 链接。

### 5. 跟进 CI

记录 `git rev-parse <分支>`，用 `gh pr view <编号> --json headRefOid,statusCheckRollup,mergeStateStatus` 和 `gh pr checks <编号>` 检查对应 HEAD。等待期间持续报告有意义的进展；每次等待不超过 60 秒。失败时读取失败 job 日志，区分本次缺陷、既有失败和基础设施阻塞。

本次缺陷由作者修复，相关检查通过后提交，由 [accept](../accept/SKILL.md) 复查新 commit diff 和受影响回归，通过后 push 并检查新 HEAD；同一交付累计最多三轮独立审查。禁止跳过检查、放宽断言或反复重跑掩盖根因。无可执行修复或达到上限时保留工作区并报告。

完成标准：已核实当前 HEAD 的必过检查通过，或明确记录失败、受阻、等待、跳过、没有配置检查；后五者均不宣称 CI 全绿。不自动合并。

### 6. 汇报

告诉用户 PR 链接、分支、HEAD、CI 结果和剩余问题；合并由用户决定。

## 示例

mode 完成 feature 后读取本 skill：分支是集成分支 `jstack/spec-12`，`git log main..jstack/spec-12` 列出 6 个 commit；默认连续交付；账号检查通过；push 后没有已有 PR，用 mode 的三段汇报作正文创建 PR。

结果：返回 PR 链接和当前 HEAD 的 CI 结果，合并由用户决定。

用户说"把当前分支提个 PR"：分支是 `jstack/fix-csv-last-row`，检查账号、push，按 `git log` 写三段正文后创建 PR。

## 常见问题

现象：push 报 `Permission ... denied` 或 403。
原因：当前活跃的 gh 账号没有写权限。
处理：回到第 3 步重新检查账号；仍然失败时停下，把报错原文告诉用户。

现象：push 报 `rejected`（non-fast-forward）。
原因：远端分支有本地没有的 commit。
处理：停下，把报错和 `git log <分支>..origin/<分支>` 的结果告诉用户，由用户决定是否 rebase。

现象：`gh pr create` 报 `already exists`。
原因：这个分支已经有打开的 PR。
处理：用第 4 步的 `gh pr list` 取出链接告诉用户，不重复创建。
