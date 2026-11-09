# worktree 规则

implement 和 diagnosing-bugs 改代码前，在项目内新建 worktree 和新分支，之后只在 worktree 里改文件、运行命令和 commit。用户主目录的分支和文件保持不变。worktree 规则只写在本文件，其他 skill 链接这里。

不使用 Harness 自带的 worktree 功能：Codex 自带的只能放在用户级全局目录，Claude Code 自带的不能指定分支名和起点。

## 占位符

| 占位符 | 取值 |
|---|---|
| `<worktree 目录>` | Claude Code 为 `.claude/worktrees`，Codex 为 `.codex/worktrees`，见当前 Harness 的 adapter |
| `<主目录>` | 在用户当前目录运行 `git rev-parse --show-toplevel` 得到的绝对路径 |
| `<基准>` | 调用方给的基准分支；没给时用 `git branch --show-current` 的结果，结果为空（detached HEAD）时用 `HEAD` |
| `<新分支>` | 调用方给的分支名；没给时用 `jstack/<简短描述>`，简短描述用小写英文和连字符，例如 `jstack/fix-csv-last-row` |
| `<名称>` | `<新分支>` 中的 `/` 换成 `-`，例如 `jstack-fix-csv-last-row` |

## 开始

以下命令都以 `cd <主目录> &&` 开头。

1. 清理失效的 worktree 记录，并列出遗留的 jstack worktree：

   ```bash
   git worktree prune && git worktree list | grep -e '/.claude/worktrees/' -e '/.codex/worktrees/'
   ```

   以下 worktree 正在使用，不算遗留：分支是 `<基准>` 的 worktree（feature 的集成 worktree），以及分支以 `<基准>-t` 开头的 worktree（同一 spec 下正在进行的其他 ticket）。除去它们后没有输出，表示没有遗留。还有输出时，在收尾汇报里列出这些路径，不删除，也不复用。

2. 把两个 worktree 目录写进本地排除文件，已有的跳过。不改项目的 `.gitignore`：

   ```bash
   f="$(git rev-parse --git-common-dir)/info/exclude"; mkdir -p "$(dirname "$f")"; [ -s "$f" ] && [ -n "$(tail -c1 "$f")" ] && echo >> "$f"; for p in .claude/worktrees/ .codex/worktrees/; do grep -qxF "$p" "$f" 2>/dev/null || echo "$p" >> "$f"; done
   ```

3. 记下起点 commit，然后创建 worktree 和新分支：

   ```bash
   git rev-parse <基准>
   git worktree add <worktree 目录>/<名称> -b <新分支> <基准>
   ```

   `<新分支>` 已存在时创建会失败：换一个简短描述重试，不删除已有分支。

4. 之后每条命令都以 `cd <主目录>/<worktree 目录>/<名称> &&` 开头，不在主目录改文件或 commit。主目录里未提交的改动不会出现在 worktree 中；任务依赖这些改动时，在汇报里写明。

调用方给了已有的 worktree 路径和起点时（例如重试），跳过以上步骤，直接在这个 worktree 里工作。

完成标准：能汇报三项——worktree 绝对路径、新分支名、起点 commit。

## 集成 worktree

feature playbook 的集成分支也放在 worktree 里，用户主目录的当前分支始终不变。

1. to-spec 发布 spec 后，按"开始"一节建集成 worktree：`<名称>` 为 `jstack-spec-<spec 编号>`，`<新分支>` 为 `jstack/spec-<spec 编号>`，`<基准>` 是主目录的当前分支。
2. 每张 ticket 按"开始"一节建自己的 worktree，`<基准>` 是集成分支 `jstack/spec-<spec 编号>`。
3. 合并 ticket 分支、波次全量测试都在集成 worktree 里执行，每条命令都以 `cd <集成 worktree 绝对路径> &&` 开头，例如：

   ```bash
   cd <集成 worktree 绝对路径> && git merge --no-ff <ticket 分支>
   ```

完成标准：集成 worktree 的绝对路径已记下；主目录的当前分支和工作区没有变化。

## 清理

以下命令都以 `cd <主目录> &&` 开头，不能在要删除的 worktree 里执行。

删除 worktree：

```bash
git worktree remove <worktree 目录>/<名称>
```

需要删除分支时，再运行：

```bash
git branch -d <新分支>
```

`git branch -d` 按当前目录的 HEAD 判断分支是否已合并。feature ticket 的分支只合并进了集成分支，在主目录删除会报 not fully merged，所以在集成 worktree 里删除它；ticket 的 worktree 仍在主目录用 `git worktree remove` 删除：

```bash
cd <主目录> && git worktree remove <worktree 目录>/<名称>
cd <集成 worktree 绝对路径> && git branch -d <新分支>
```

worktree 有未提交的改动时 `git worktree remove` 会失败，分支未合并时 `git branch -d` 会失败。失败时不加 `--force` 或 `-D`，保留它们，并在汇报里列出。

| 场景 | 清理时机 | 由谁清理 | worktree | 分支 |
|---|---|---|---|---|
| 单独使用 implement 或 diagnosing-bugs | accept 结论为 PASS 或 PASS+NOTES | implement 或 diagnosing-bugs 自己 | 删除 | 保留，告诉用户分支名 |
| bug-fix playbook | accept 结论为 PASS 或 PASS+NOTES | j-mode | 删除 | 保留，告诉用户分支名 |
| feature playbook 的 ticket | 合并进集成分支之后 | j-mode | 删除 | 删除 |
| feature playbook 的集成 worktree | j-mode 收尾之后 | j-mode | 删除 | 保留，告诉用户分支名 |
| 以上任一场景，最终结论为 FAIL | 不清理 | — | 保留 | 保留 |

保留下来的 worktree，在收尾汇报里列出路径，以及供用户自己运行的删除命令：

```bash
git worktree remove --force <worktree 绝对路径> && git branch -D <新分支>
```
