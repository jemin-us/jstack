---
name: j-mode
description: 当用户提出泛化的开发请求时使用，例如“加个功能”“给订单列表加按状态筛选”“改一下这个行为”“修这个 bug”。按 jstack 工作流判断规模和类型：需要 spec 或要拆成多张 ticket 的功能走 feature playbook，bug 走 bug-fix playbook，一个 ticket 就能做完的小改动（例如“给脚本加个参数”）交给 implement，依次执行其他 jstack skill 完整推进。请求已指明 ticket 编号、spec 编号或待验收的分支时，使用对应的 implement、to-tickets、accept。
---

# jstack 入口

## 硬性规则

- `<jstack 插件目录>` 是本文件所在目录往上两级（本文件位于 `<jstack 插件目录>/skills/j-mode/SKILL.md`）。开始时确定一次它的绝对路径，之后读取其他 skill、填写 brief 都用这个绝对路径。
- 先读取当前 Harness 的 adapter，整个会话只读一次：[Claude Code](references/harness/claude-code.md)、[Codex](references/harness/codex.md)。下文的"读取 skill""派 subagent""向用户提问"都按 adapter 执行。
- 执行其他 jstack skill 的方式是读取它的 `SKILL.md` 并照做。
- 选定 playbook 后，把它的步骤原样抄进任务列表。不做的步骤保留在列表里，标为"跳过：<原因>"。
- 回复中的每个论断都要标明证据等级：已运行、推断、未验证。自己能跑的检查不交给用户。
- 只在非默认分支上 commit。push 和开 PR 在第 4 步先问用户，用户同意后才执行。
- 写入 GitHub（push、开 PR、创建或修改 issue）前，运行 `gh api repos/<owner/repo> --jq .permissions.push` 确认当前 gh 账号有写权限，`<owner/repo>` 用 `gh repo view --json nameWithOwner --jq .nameWithOwner` 查。结果是 `true` 时继续；否则按 [setup-jstack](../setup-jstack/SKILL.md) 第 3 步找出已登录且有写权限的账号，运行 `gh auth switch -u <账号>`，并告诉用户切到了哪个账号；找不到这样的账号时停下，请用户自己运行 `gh auth login`。
- issue 状态只由 j-mode 修改，规则和命令见 [references/issue-state.md](references/issue-state.md)。不加标签。
- 验收结论只来自 accept，作者不能给自己出结论。

## 流程

### 1. 选 playbook

根据用户请求，从下表中选一个：

| playbook | 适用 | 执行方式 |
|---|---|---|
| feature | 需要拆成多张 ticket 或需要 spec 的新功能、行为变更 | [feature.md](references/playbooks/feature.md) |
| change | 一个 ticket 就能做完、不需要 spec 的改动 | 读取 [implement](../implement/SKILL.md) 并照做，不创建 issue |
| bug-fix | 现有行为出错、报错、性能退化 | [bug-fix.md](references/playbooks/bug-fix.md) |

完成标准：向用户说明选了哪个 playbook，并给出一句理由。选 change 时，向用户说明这次交给 implement，最终汇报里也写明由 implement 完成；implement 自己建 worktree、实现、accept 和清理，读取它的 `SKILL.md` 并照做后不再执行下面的步骤。都不适用时，说明改用哪个 jstack skill，然后直接读取它的 `SKILL.md` 并照做，不再执行下面的步骤。

### 2. 准备分支

三个 playbook 都不切换主目录的分支。

- feature：按 [worktree.md](../implement/references/worktree.md) 的"集成 worktree"一节新建集成 worktree 和集成分支 `jstack/spec-<spec 编号>`，各 ticket 的改动最后都合并到这里。spec 编号在 to-spec 发布后才有，所以这一步放到 to-spec 之后执行。
- bug-fix：worktree 和新分支由 bug-fix playbook 第 1 步建。
- change：worktree 和新分支由 implement 建。

完成标准：feature 的集成 worktree 已建好，记下它的绝对路径；三个 playbook 下主目录的分支都保持不变。

### 3. 执行 playbook

读取选定的 playbook 文件，按步骤执行。每完成一步，就在任务列表里勾掉它。

完成标准：playbook 的每一步都已完成，或已标为跳过并写明原因。

### 4. 收尾

按以下三段汇报：

```markdown
**改了什么**
- 每张 ticket（或这次修复）：行为变化、commit 范围

**验证了什么**
- 每张 ticket 的 accept 结论（PASS / PASS+NOTES / FAIL）和关键证据（已运行）

**还有什么**
- 受阻的验收检查，以及原因
- subagent 做出的假设、选定的测试接缝
- 仍为 open 的 issue 及其状态（验收失败 / 待人工验收）
- 跳过的步骤和原因
```

汇报后问用户一次："要 push `<分支>` 并开 PR 吗？"`<分支>` 在 feature 下是集成分支 `jstack/spec-<spec 编号>`，在 bug-fix 下是修复分支。以下命令都以 `cd <主目录> &&` 开头。

- 用户同意：按硬性规则检查账号，然后运行 `git push -u origin <分支>`，再运行 `gh pr create --base <默认分支> --head <分支> --title "<标题>" --body-file "$f"`，正文是上面的三段汇报，先写进 `f=$(mktemp)`。`<默认分支>` 用 `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name` 查。把 PR 链接告诉用户，PR 由用户自己合并。
- 用户不同意：保留本地分支，告诉用户分支名。

之后，feature 按 [worktree.md](../implement/references/worktree.md) "清理"一节中"feature playbook 的集成 worktree"一行删除集成 worktree、保留集成分支。

完成标准：用户已回答是否 push；同意时 PR 已创建，链接已告诉用户；feature 的集成 worktree 已删除。

## 示例

用户说："/jstack:j-mode 给订单列表加按状态筛选"

执行：选择 feature；用 brainstorm 追问两轮；用 to-spec 发布 spec #12，在集成 worktree 里新建分支 `jstack/spec-12`；用 to-tickets 拆出互不阻塞的 #13、#14；两张在各自的 worktree 里并行实现；#13 验收 PASS 后合并；#14 第一次 accept 判 FAIL，带上失败输出重新派一次 subagent，第二次判 PASS 后合并；集成分支全量测试通过。

结果：#13、#14 评论了验收结论并关闭，#12 随之关闭；按三段式汇报；用户同意 push 后，开出 `jstack/spec-12` 到默认分支的 PR，删除集成 worktree。

## 常见问题

现象：同一张 ticket 第二次 accept 仍为 FAIL。
原因：ticket 切分有问题，或者验收检查本身写错了。
处理：停止后续 ticket，把两次 FAIL 的证据交给用户，由用户决定是修改 ticket 还是自己介入。
