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

### 2. 询问

自动执行时，或用户直接要求 push 或开 PR 时，跳过本步。

其余情况，即不是自动执行、由 finish 读取本 skill 时：问用户一次"要 push `<分支>` 并开 PR 吗？"。用户不同意时，告诉用户分支名并结束。

完成标准：用户已同意，或本步已跳过。

### 3. 检查账号并 push

1. 按 [setup](../setup/SKILL.md) 的"写入 GitHub 前检查账号"一节确认当前 gh 账号有写权限。
2. 运行 `git push -u origin <分支>`。

完成标准：push 成功，`git status -sb` 显示分支与远端同步。

### 4. 开 PR

1. 运行 `gh pr list --head <分支> --json url --jq '.[].url'`。有输出说明 PR 已存在，把链接告诉用户，跳到第 5 步。
2. 准备标题和正文：调用方给了收尾汇报时，正文用它；用户直接要求时，根据 `git log <默认分支>..<分支>` 写"改了什么、验证了什么、还有什么"三段，没跑过的检查标"未验证"。标题用一句话概括这些 commit。
3. 正文写进 `f=$(mktemp)`，运行：

   ```bash
   gh pr create --base <默认分支> --head <分支> --title "<标题>" --body-file "$f"
   ```

完成标准：拿到 PR 链接。

### 5. 汇报

告诉用户 PR 链接、分支名，以及合并由用户决定。

## 示例

mode 完成 feature 后读取本 skill：分支是集成分支 `jstack/spec-12`，`git log main..jstack/spec-12` 列出 6 个 commit；自动执行，跳过询问；账号检查通过；push 后没有已有 PR，用 mode 的三段汇报作正文创建 PR。

结果：返回 PR 链接，提醒合并由用户决定。

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
