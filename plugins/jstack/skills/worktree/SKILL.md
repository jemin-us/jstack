---
name: worktree
description: 在项目内新建和清理 jstack 的 git worktree 与分支，并把多个分支合并到集成 worktree。implement、diagnosing-bugs、mode 改代码前读取，mode、finish 验收后读取，不单独使用。
disable-model-invocation: true
---

# worktree

改代码前，在项目内新建 worktree 和新分支，之后只在 worktree 里改文件、运行命令和 commit。本 skill 提供三个操作：开始、集成 worktree、清理。调用方指定用哪个操作，以及何时清理。

## 硬性规则

- 用户主目录的分支和文件保持不变：不切换分支，不在主目录改文件或 commit。
- 用 git 命令自建 worktree，不使用 Harness 自带的 worktree 功能：Codex 自带的只能放在用户级全局目录，Claude Code 自带的不能指定分支名和起点。
- 删除失败时保留现场并汇报，不加 `--force` 或 `-D`。

## 占位符

| 占位符 | 取值 |
|---|---|
| `<worktree 目录>` | Claude Code 为 `.claude/worktrees`，Codex 为 `.codex/worktrees` |
| `<主目录>` | 在用户当前目录运行 `git rev-parse --show-toplevel` 得到的绝对路径 |
| `<基准>` | 调用方给的基准分支；没给时用 `git branch --show-current` 的结果，结果为空（detached HEAD）时用 `HEAD` |
| `<新分支>` | 调用方给的分支名；没给时用 `jstack/<简短描述>`，简短描述用小写英文和连字符，例如 `jstack/fix-csv-last-row` |
| `<名称>` | `<新分支>` 中的 `/` 换成 `-`，例如 `jstack-fix-csv-last-row` |

## 开始

以下命令都以 `cd <主目录> &&` 开头。

0. 检查 `git status --short`、当前分支、worktree 和已有 PR，记录暂存、未暂存及未跟踪内容。涉及多人协作或远程进展时 fetch 并比较基准与远程差异，不自动 pull。任务依赖未提交内容时先确定如何保留并带入所需基线；不能只建一个缺少依赖的 worktree 然后继续。无法安全确定基线时说明阻塞，不覆盖、stash 或丢弃已有修改。

1. 清理失效的 worktree 记录，并列出遗留的 jstack worktree：

   ```bash
   git worktree prune && git worktree list | grep -e '/.claude/worktrees/' -e '/.codex/worktrees/'
   ```

   以下 worktree 正在使用，不算遗留：分支是 `<基准>` 的 worktree（集成 worktree），以及分支以 `<基准>-t` 开头的 worktree（同一集成分支下正在进行的其他 ticket）。除去它们后没有输出，表示没有遗留。还有输出时，在收尾汇报里列出这些路径，不删除，也不复用。

2. 把两个 worktree 目录写进本地排除文件，已有的跳过。不改项目的 `.gitignore`：

   ```bash
   f="$(git rev-parse --git-common-dir)/info/exclude"; mkdir -p "$(dirname "$f")"; [ -s "$f" ] && [ -n "$(tail -c1 "$f")" ] && echo >> "$f"; for p in .claude/worktrees/ .codex/worktrees/; do grep -qxF "$p" "$f" 2>/dev/null || echo "$p" >> "$f"; done
   ```

3. 记下起点 commit，然后创建 worktree 和新分支：

   ```bash
   git rev-parse <基准>
   git worktree add <worktree 目录>/<名称> -b <新分支> <基准>
   ```

4. 之后每条命令都以 `cd <主目录>/<worktree 目录>/<名称> &&` 开头。主目录里未提交的改动不会自动出现在 worktree 中；确认第 0 步确定的任务基线在这里完整可用。

调用方给了已有的 worktree 路径和起点时（例如重试），跳过以上步骤，直接在这个 worktree 里工作。

完成标准：能汇报三项——worktree 绝对路径、新分支名、起点 commit。

## 集成 worktree

调用方要把多个分支合并到一个集成分支时使用。集成分支也放在 worktree 里。

1. 按"开始"一节建集成 worktree：`<新分支>` 是调用方给的集成分支名，`<基准>` 是主目录的当前分支。
2. 每个要合并的分支按"开始"一节建自己的 worktree，`<基准>` 是集成分支，`<新分支>` 命名为 `<集成分支>-t<编号>`。"开始"第 1 步靠这个前缀识别正在进行的分支。
3. 合并和全量测试都在集成 worktree 里执行，每条命令都以 `cd <集成 worktree 绝对路径> &&` 开头，例如：

   ```bash
   cd <集成 worktree 绝对路径> && git merge --no-ff <要合并的分支>
   ```

完成标准：集成 worktree 的绝对路径已记下；主目录的当前分支和工作区没有变化。

## 清理

以下命令都以 `cd <主目录> &&` 开头，不能在要删除的 worktree 里执行。

删除 worktree：

```bash
git worktree remove <worktree 目录>/<名称>
```

调用方要求删除分支时，再运行：

```bash
git branch -d <新分支>
```

`git branch -d` 按当前目录的 HEAD 判断分支是否已合并。只合并进了集成分支的分支，要在集成 worktree 里删除；它的 worktree 仍在主目录删除：

```bash
cd <主目录> && git worktree remove <worktree 目录>/<名称>
cd <集成 worktree 绝对路径> && git branch -d <新分支>
```

保留下来的 worktree，在收尾汇报里列出路径。只有确认成果已保存且没有未提交文件后，才可使用下列命令清理；不建议强制删除：

```bash
git worktree remove <worktree 绝对路径>
```

完成标准：`git worktree list` 里没有已删除的 worktree；保留下来的 worktree 和分支都已写进汇报。

## 示例

implement 要实现 #42，没有给基准和分支名：主目录当前分支是 `main`，`<新分支>` 取 `jstack/health-check`，`<名称>` 是 `jstack-health-check`；按"开始"一节建出 `.claude/worktrees/jstack-health-check`，记下起点 commit；验收通过后 implement 要求删除 worktree、保留分支，按"清理"一节运行 `git worktree remove`。

结果：主目录仍在 `main` 且没有改动，分支 `jstack/health-check` 保留。

## 常见问题

现象：`git worktree add` 报 `a branch named ... already exists`。
原因：`<新分支>` 已存在。
处理：换一个简短描述重试，不删除已有分支。

现象：`git worktree remove` 报 `contains modified or untracked files`。
原因：worktree 里有未提交的改动。
处理：保留 worktree，在汇报里列出路径和上面的删除命令。

现象：`git branch -d` 报 `not fully merged`。
原因：分支没有合并进当前目录的 HEAD。
处理：分支只合并进了集成分支时，改在集成 worktree 里删除；确实没有合并时保留分支，并在汇报里列出。
