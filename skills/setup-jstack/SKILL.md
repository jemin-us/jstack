---
name: setup-jstack
description: 当任务涉及在项目中启用 jstack、检查 git 与 gh 环境、配置 GitHub issue 仓库和标签时使用。为项目生成验证 skill 使用 create-verify-app。
disable-model-invocation: true
---

# 配置项目

## 硬性规则

- 安装工具、写 `AGENTS.md`、创建标签都会改动用户环境。每做一项之前，先展示具体命令或内容，得到用户确认后再执行。
- `gh auth login` 只能由用户本人运行。agent 不代为输入任何账号、密码或 token。
- 不修改 `CLAUDE.md`，只提示用户自己去改。
- 本 skill 可以重复运行，结果不变：已满足的项跳过，`## jstack` 块原地更新，不追加第二份。本次运行中用户拒绝过的事，不再追问。
- 开始前读取当前 Harness 对应的 Adapter：[Claude Code](../j-mode/references/harness/claude-code.md)、[Codex](../j-mode/references/harness/codex.md)。

## 流程

### 1. 检查环境

在项目根目录运行只读检查脚本。脚本不修改任何东西：

```bash
python3 <本 skill 目录>/scripts/check_env.py .
```

每行输出一个检查项，格式是 `<检查项>=<结果>`。各项含义见 [references/check-items.md](references/check-items.md)。

完成标准：拿到全部检查项的结果，并列出哪些不满足。

### 2. 安装缺失的工具

`git=missing` 或 `gh=missing` 时，按用户的平台给出安装命令。macOS 用 `brew install gh`，其他平台见 [references/check-items.md](references/check-items.md)。命令得到用户确认后再执行。

`gh_features` 缺少 `--blocked-by` 或 `--parent` 时，说明 `gh` 版本太旧，不支持建子 issue 和阻塞关系。给出升级命令，例如 `brew upgrade gh`，同样确认后再执行。

完成标准：重新运行脚本，`git`、`gh`、`gh_features` 都是 `ok`；或者用户拒绝安装，此时停止，并说明 to-spec 和 to-tickets 无法使用。

### 3. 确认登录和仓库

- `gh_auth=not_logged_in`：请用户在自己的终端运行 `gh auth login`，用户回复完成后，再运行一次脚本确认结果。
- `github_remote=none`：告诉用户当前项目没有 GitHub remote，jstack 的 issue 流程无法使用。停止，不替用户建仓库。

- `gh_permission=insufficient <权限>`：当前活跃的 gh 账号对这个仓库没有写权限。请用户运行 `gh auth status` 查看已登录的账号，在自己的终端用 `gh auth switch -u <账号>` 切到有权限的账号，再运行一次脚本。

完成标准：`gh_auth=ok`、`gh_permission=ok`，并且 `github_remote` 是 `owner/repo` 格式。

### 4. 写入配置

1. 按 [references/agents-block.md](references/agents-block.md) 生成 `## jstack` 块的草稿，填入步骤 3 得到的 `owner/repo`。
2. 向用户展示草稿。用户确认或修改后，按 `agents_md` 的结果写入：
   - `absent`：新建 `AGENTS.md`，内容只有这一块。
   - `no_jstack_block`：在文件末尾追加这一块，不改动文件里其他内容。
   - `has_jstack_block`：用草稿原地替换原有的块，块外内容保持不变。
3. `labels` 缺少标签时，列出要执行的 `gh label create` 命令（命令见 references），用户确认后执行。

完成标准：重新运行脚本，`agents_md=has_jstack_block`，`labels=ok`。

### 5. 检查 CLAUDE.md

`claude_md=missing_import` 时，告诉用户：Claude Code 在有 `CLAUDE.md` 的项目里不会读取 `AGENTS.md`，所以需要在 `CLAUDE.md` 中加一行 `@AGENTS.md`。不要自己修改这个文件。

完成标准：已经提示过用户；`absent` 或 `imports_agents` 时跳过这一步。

### 6. 询问验证 skill

检查项目里是否已有 `verify-` 开头的 skill，查 `.agents/skills/` 和 `.claude/skills/` 两个目录。没有的话，问用户一次："要不要生成一个项目专用的验证 skill，让 agent 能像用户一样启动和操作 app？"

- 用户同意：读取 jstack skill create-verify-app 并执行。
- 用户拒绝：结束，不再追问。

完成标准：已经问过，或者项目里已有 verify skill。

### 7. 汇报

按"改了什么 / 验证了什么 / 还有什么"三段汇报。"还有什么"列出用户拒绝的项和仍不满足的检查项。

## 示例

用户说："/jstack:setup-jstack"
执行：1. 运行脚本，结果是 `labels=missing jstack:spec,jstack:ticket`、`agents_md=absent`，其余都是 `ok`；2. 展示 `## jstack` 块草稿，用户确认后新建 `AGENTS.md`；3. 展示两条 `gh label create` 命令，用户确认后执行；4. 再跑一次脚本，全部是 `ok`；5. 询问是否生成 verify skill，用户拒绝。
结果：`AGENTS.md` 中有了 `## jstack` 块，仓库新增了两个标签。

## 常见问题

现象：`gh_auth=not_logged_in`，但用户说已经登录。
原因：`gh` 登录了多个账号，当前活跃账号没有这个仓库的权限，或者 token 已过期。
处理：请用户运行 `gh auth status` 查看活跃账号，必要时用 `gh auth switch` 切换，然后重新运行脚本。

现象：`labels=unknown`。
原因：`gh label list` 失败，通常是没有网络，或者当前账号没有这个仓库的读取权限。
处理：先解决网络或权限问题，再重新运行脚本。不要在拿不到标签列表的情况下直接创建标签。

现象：`gh label create` 报错，提示没有权限。
原因：当前账号对仓库只有读权限。
处理：请用户切换到有写权限的账号，或者让仓库所有者创建标签。
