# jstack

个人工程工作流插件，Claude Code 和 Codex 共用一份源码。

## 安装

Claude Code：

```bash
claude plugin marketplace add jemin-us/jstack
claude plugin install jstack@jstack
```

Codex 通过仓库中的 `.claude-plugin/marketplace.json` 识别本插件。

## Skills

除 `worktree`、`harness` 和 `finish` 外，所有 skill 都会按请求自动加载，也可以用 `/jstack:<名称>` 手动调用。这三个只供其他 skill 读取，不自动加载。泛化的新功能和 bug 请求由入口 `mode` 承接；指明 ticket 编号、spec 编号或待验收分支的请求直接加载对应的 skill。`mode` 发起的流程自动执行：只在开头问一轮难以回头的决定，之后直接发布 spec 和 ticket、push 并开 PR，合并由用户决定；单独调用某个 skill 时保留发布前的确认。

适用范围：一张 ticket 大小及以上的改动走 jstack，在 worktree 里实现并独立验收。改一行、改个文案这类很小的改动，agent 可能直接修改，不经过 jstack。

| skill | 职责 |
|---|---|
| `mode` | 入口，选 playbook 并按步骤调用其他 skill |
| `brainstorm` | 需求追问 |
| `to-spec` | 生成 spec 并发布为 GitHub issue |
| `to-tickets` | 拆成可独立执行的 ticket |
| `implement` | 测试先行地实现并 commit |
| `diagnosing-bugs` | 复现、定位并修复 bug |
| `accept` | 非作者 agent 独立验收 |
| `pr` | push 已 commit 的分支并开 PR |
| `create-verify-app` | 为项目生成 verify-app 类 skill |
| `setup` | 检查 gh 环境、账号和默认仓库，生成项目的验证 skill |
| `help` | 说明该用哪个 skill、怎么调用 |
| `skill-creator-plus` | 新建、修改和审查 skill |
| `writing-for-agents` | 编写和审查给 agent 读的文字 |
| `worktree` | 新建和清理项目内的 git worktree，把多个分支合并到集成 worktree，供其他 skill 读取 |
| `harness` | 通用说法在 Claude Code 和 Codex 中的对应操作，供其他 skill 读取 |
| `finish` | implement、diagnosing-bugs 单独使用时的验收、清理和开 PR，供其他 skill 读取 |

## 开发

```bash
python3 scripts/validate.py
```

skill 之间只能引用对方的 `SKILL.md`，不能引用对方的 `references/`、`scripts/` 等内部文件；多个 skill 共用的内容抽成单独的 skill。`scripts/validate.py` 会检查这一条。

术语见 `GLOSSARY.md`。
