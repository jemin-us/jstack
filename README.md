# jstack

个人工程工作流插件，Claude Code 和 Codex 共用一份源码。流程参考 mattpocock/skills 与 cursor/plugins 的 pstack。

## 安装

Claude Code：

```bash
claude plugin marketplace add jemin-us/jstack
claude plugin install jstack@jstack
```

Codex 通过仓库中的 `.claude-plugin/marketplace.json` 识别本插件。

## Skills

所有 skill 都会按请求自动加载，也可以用 `/jstack:<名称>` 手动调用。泛化的新功能和 bug 请求由入口 `j-mode` 承接；指明 ticket 编号、spec 编号或待验收分支的请求直接加载对应的 skill。

适用范围：一张 ticket 大小及以上的改动走 jstack，在 worktree 里实现并独立验收。改一行、改个文案这类很小的改动，agent 可能直接修改，不经过 jstack。

| skill | 职责 |
|---|---|
| `j-mode` | 入口，选 playbook 并按步骤调用其他 skill |
| `brainstorm` | 需求追问 |
| `to-spec` | 生成 spec 并发布为 GitHub issue |
| `to-tickets` | 拆成可独立执行的 ticket |
| `implement` | 测试先行地实现并 commit |
| `diagnosing-bugs` | 复现并定位 bug |
| `accept` | 非作者 agent 独立验收 |
| `pr` | push 已 commit 的分支并开 PR |
| `create-verify-app` | 为项目生成 verify-app 类 skill |
| `setup-jstack` | 检查 gh 环境、账号和默认仓库 |
| `skill-creator-plus` | 新建、修改和审查 skill |
| `writing-for-agents` | 编写和审查给 agent 读的文字（中文改写版） |

## 开发

```bash
python3 scripts/validate.py
```

设计决策见 `docs/adr/`，术语见 `GLOSSARY.md`。
