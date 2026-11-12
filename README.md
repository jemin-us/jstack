# jstack

个人工程工作流插件，Claude Code 和 Codex 共用一份源码。

## 安装

Claude Code（更新：`claude plugin marketplace update jstack && claude plugin update jstack@jstack`）：

```bash
claude plugin marketplace add jemin-us/jstack
claude plugin install jstack@jstack
```

Codex（更新：`codex plugin marketplace upgrade jstack && codex plugin add jstack@jstack`）：

```bash
codex plugin marketplace add jemin-us/jstack
codex plugin add jstack@jstack
```

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
| `codebase` | 把项目的形状规则落成会失败的检查，接进 CI，已有违规冻结成基线 |
| `codebase-audit` | 只读审计一块代码的结构问题，输出按修法组织的清单，每个修法标明能否配检查 |
| `setup` | 检查 gh 环境、账号和默认仓库，生成项目的验证 skill |
| `help` | 说明该用哪个 skill、怎么调用 |
| `skill-creator-plus` | 新建、修改和审查 skill |
| `writing-for-agents` | 编写和审查给 agent 读的文字 |
| `worktree` | 新建和清理项目内的 git worktree，把多个分支合并到集成 worktree，供其他 skill 读取 |
| `harness` | 通用说法在 Claude Code 和 Codex 中的对应操作，供其他 skill 读取 |
| `finish` | implement、diagnosing-bugs 单独使用时的验收、清理和开 PR，供其他 skill 读取 |

## 开发

```bash
make test        # 校验 skill 结构和生成文件
make regenerate  # 改了 VERSION 或 skills/ 后重新生成两端的清单和 Codex 镜像
```

版本号只改 `VERSION`。`.claude-plugin/`、`.agents/`、`plugins/jstack/` 都是生成的，不要手改。仓库结构、开发和发布规则见 `AGENTS.md`。
