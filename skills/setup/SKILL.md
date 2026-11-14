---
name: setup
description: 当任务涉及在项目中启用 jstack、检查 git 与 gh 环境、确认 GitHub 账号和默认仓库时使用。运行只读检查脚本，补齐 gh 安装、账号写权限和默认仓库，项目没有验证 skill 时生成一个。只生成或更新验证 skill 使用 create-verify-app。
---

# 配置项目

## 硬性规则

- `gh auth login` 只能由用户本人运行。agent 不代为输入任何账号、密码或 token。
- 本 skill 可以重复运行，结果不变：已满足的项直接跳过。

## 流程

### 1. 检查环境

在项目根目录运行只读检查脚本：

```bash
python3 <本 skill 目录>/scripts/check_env.py .
```

输出的格式和各检查项的含义见 [references/check-items.md](references/check-items.md)。

完成标准：拿到全部检查项的结果，并列出哪些不满足。

### 2. 安装或升级 gh

- `gh=missing`：给出 `brew install gh`，用户确认后执行。
- `gh_features` 缺少 `--blocked-by` 或 `--parent`：gh 版本太旧，给出 `brew upgrade gh`，用户确认后执行。

完成标准：重新运行脚本，`gh`、`gh_features` 都是 `ok`。

### 3. 确认账号

- `gh_auth=not_logged_in`：请用户在自己的终端运行 `gh auth login`，用户回复完成后重新运行脚本。
- `gh_permission=insufficient <权限>`：当前活跃账号对仓库没有写权限。自己排查：运行 `gh auth status` 列出已登录的账号，找出仓库 owner 对应的账号，或对仓库有写权限的账号，然后运行 `gh auth switch -u <账号>` 切换，并告诉用户切到了哪个账号。Harness 不允许切换时，把这条命令交给用户运行。

完成标准：`gh_auth=ok`，`gh_permission=ok`。

### 4. 指定默认仓库

`default_repo=unset` 表示项目有多个 GitHub remote，gh 不知道 issue 该发到哪个仓库。列出 `github_remote` 中的候选仓库，问用户用哪一个，然后运行 `gh repo set-default <owner/repo>`。只有一个 GitHub remote 时跳过本步。

完成标准：脚本输出 `result=ok`。

### 5. 生成验证 skill

检查项目里是否已有 `verify-` 开头的 skill：

```bash
ls -d .agents/skills/verify-* .claude/skills/verify-* 2>/dev/null
```

没有输出时，读取 [create-verify-app](../create-verify-app/SKILL.md) 并照做。项目没有可以启动的使用面（例如只有文档）时跳过，在汇报的"还有什么"里写明。

完成标准：项目里有 verify skill，或者已写明跳过的原因。

### 6. 汇报

按 [harness](../harness/SKILL.md) 的三段汇报。

## 写入 GitHub 前检查账号

其他 jstack skill 在 push、开 PR、创建或修改 issue 之前读取本节。运行：

```bash
gh api repos/$(gh repo view --json nameWithOwner --jq .nameWithOwner) --jq .permissions.push
```

输出 `true` 时继续。否则按第 3 步找出有写权限的已登录账号，运行 `gh auth switch -u <账号>`，并告诉用户切到了哪个账号；没有这样的账号时停下，请用户自己运行 `gh auth login`。

完成标准：上面的命令输出 `true`。

## 示例

用户说："/jstack:setup"

执行：运行脚本，结果是 `gh_permission=insufficient READ`；`gh auth status` 显示另一个已登录账号 `jemin-us` 正是仓库 owner，运行 `gh auth switch -u jemin-us`；重新运行脚本，`result=ok`；项目里没有 verify skill，按 create-verify-app 生成 `verify-shop4-web` 并跑通。

结果：活跃账号切换为 `jemin-us`，项目可以使用 `spec` 和 `tickets`，accept 验收时有 `verify-shop4-web` 可读。

## 常见问题

现象：脚本输出 `github_remote=none`。
原因：项目没有指向 GitHub 的 remote，而 spec 和 ticket 都发布为 GitHub issue。
处理：停下，请用户运行 `git remote add origin <仓库地址>`，完成后重新运行脚本。

现象：切换账号后 `gh_permission` 仍是 `insufficient`。
原因：已登录的账号对这个仓库都没有写权限。
处理：停下，告诉用户仓库名和缺少的权限，请用户自己运行 `gh auth login` 登录有权限的账号，或向仓库 owner 申请权限。
