# implement subagent 的 brief

j-mode 派 subagent 实现一张 ticket 时，填好下面的内容，整段作为任务说明传过去。不要附带对话记录。

```markdown
你负责实现 GitHub issue #<ticket 编号>，仓库是 <owner/repo>，工作目录是 <这张 ticket 的 worktree 绝对路径>，当前分支是 <ticket 分支名>。

1. 先完整读取 <jstack 插件目录>/skills/implement/SKILL.md，然后按它执行。
2. 用 `gh issue view <ticket 编号> --json title,body,comments` 读取 ticket。
3. 你无法向用户提问。遇到歧义时，按最保守的理解实现，并把假设写进汇报。
4. 你启动时的目录不是这个 worktree，每条命令都以 `cd <worktree 绝对路径> &&` 开头。只在这个 worktree 的当前分支 commit。不切换分支，不改动其他目录，不 push，不开 PR，不修改 issue。
5. 按 implement 的收尾格式汇报，内容包括 commit 哈希、每条验收检查的实际输出、所做的假设和选定的测试接缝。

<仅重试时附上：上一次 accept 的失败详情，或合并冲突的文件列表；合并冲突时要求先 rebase 到集成分支 <集成分支名> 最新的 commit 再解决冲突>
```

`<jstack 插件目录>` 填 j-mode 开始时确定的绝对路径，也就是 j-mode 的 `SKILL.md` 所在目录往上两级。
