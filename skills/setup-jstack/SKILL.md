---
name: setup-jstack
description: 当任务涉及在项目中启用 jstack、检查 git 与 gh 环境、确认 GitHub 账号和默认仓库时使用。为项目生成验证 skill 使用 create-verify-app。
---

# 配置项目

## 硬性规则

- 安装或升级工具前，先展示命令，得到用户确认后再执行。
- `gh auth login` 只能由用户本人运行。agent 不代为输入任何账号、密码或 token。
- 不写 `AGENTS.md`、`CLAUDE.md` 或其他配置文件。gh 根据 git remote 识别仓库，多个 remote 时用 `gh repo set-default` 指定。
- 本 skill 可以重复运行，结果不变：已满足的项直接跳过。

## 流程

### 1. 检查环境

在项目根目录运行只读检查脚本：

```bash
python3 <本 skill 目录>/scripts/check_env.py .
```

每行输出一个检查项，格式是 `<检查项>=<结果>`。各项含义见 [references/check-items.md](references/check-items.md)。

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

### 5. 询问验证 skill

检查项目里是否已有 `verify-` 开头的 skill，查 `.agents/skills/` 和 `.claude/skills/` 两个目录。没有的话，问用户一次："要不要生成一个项目专用的验证 skill，让 agent 能像用户一样启动和操作 app？"

- 用户同意：读取 jstack skill create-verify-app 并执行。
- 用户拒绝：结束，不再追问。

完成标准：已经问过，或者项目里已有 verify skill。

### 6. 汇报

按"改了什么 / 验证了什么 / 还有什么"三段汇报。

## 示例

用户说："/jstack:setup-jstack"

执行：运行脚本，结果是 `gh_permission=insufficient READ`；`gh auth status` 显示另一个已登录账号 `jemin-us` 正是仓库 owner，运行 `gh auth switch -u jemin-us`；重新运行脚本，`result=ok`；询问是否生成 verify skill，用户拒绝。

结果：活跃账号切换为 `jemin-us`，项目可以使用 to-spec 和 to-tickets。
