# implement subagent 的 brief

mode 派 subagent 实现一张 ticket 时，填好下面的内容，整段作为任务说明传过去。不要附带对话记录。worktree 由 implement 按 [worktree](../../worktree/SKILL.md) 创建，mode 只传基准分支和新分支名。

```markdown
你负责实现 GitHub issue #<ticket 编号>，仓库是 <owner/repo>，仓库主目录是 <主目录绝对路径>。这次由 mode 派发。

按 <jstack 插件目录>/skills/worktree/SKILL.md 的"开始"一节新建 worktree，基准分支是 <集成分支名>，新分支名是 <ticket 分支名>。<仅重试时改为：worktree 已存在，路径是 <worktree 绝对路径>，起点是 <起点 commit>，直接在其中工作。>

1. 先完整读取 <jstack 插件目录>/skills/implement/SKILL.md，然后按它执行。
2. 用 `gh issue view <ticket 编号> --json title,body,comments` 读取 ticket。
3. 你作为 subagent 执行，无法向用户提问。
4. 你启动时的目录不是这个 worktree。worktree 建好后，每条命令都以 `cd <worktree 绝对路径> &&` 开头，只在这个 worktree 的新分支上 commit。除 worktree skill 规定的步骤外，不改动主目录和其他目录，不切换主目录的分支，不 push，不开 PR，不修改 issue。
5. 不执行 accept，不清理 worktree，这两件事由 mode 负责。
6. 按 implement 的收尾格式汇报，内容包括 worktree 绝对路径、新分支名、起点 commit、commit 哈希、每条验收检查的实际输出、所做的假设和选定的测试接缝。

<仅重试时附上：上一次 accept 的失败详情，或合并冲突的文件列表；合并冲突时要求先 rebase 到集成分支 <集成分支名> 最新的 commit 再解决冲突>
```

重试时附加的失败详情等补充内容，写法按 [prompt](../../prompt/SKILL.md)。

`<jstack 插件目录>` 填 mode 开始时按 harness 确定的绝对路径。
