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

除 `worktree`、`harness`、`finish` 和 `evaluate` 外，所有 skill 都会按请求自动加载，也可以用 `/jstack:<名称>` 手动调用。前三个只供其他 skill 读取；evaluate 按用户评测请求或维护流程读取，均不自动加载。泛化的新功能和 bug 请求由入口 `mode` 承接；指明 ticket 编号、spec 编号或待验收分支的请求直接加载对应的 skill。开发任务默认连续完成实现、验证、独立审查、commit、push、PR 和 CI 跟进，不逐步请求继续。需要 spec 和 ticket 时由 mode 自动发布。只分析的请求不改代码；用户明确限定本地修改或禁止提交时按限定范围交付。合并、发布和不可恢复的数据删除不包含在默认开发流程里。

适用范围：开发任务按影响范围选择路径。局部文案或样式改动可以直接走 implement，不必创建 spec 或 ticket，但仍验证实际效果、独立审查并自动交付。只读调查和服务操作不进入开发交付流程。

质量要求：迁移调用方后删除旧路径，清理本次涉及的冗余，检查同类问题。需要持续维护代码基线时，mode 执行维护流程：审计、分批重构、验证、独立审查、收紧基线、PR。只减不增的基线用于迁移，不代替清理；重要规则优先由结构、类型、测试和 CI 强制。

设计参考：[pstack](https://github.com/cursor/plugins/tree/main/pstack) 的自动执行、先减后加和可验证交付，以及 [Waza AI Coding 军规](https://github.com/tw93/Waza/blob/main/docs/ai-coding-rules.zh.md) 的职责分离、脚本约束和反馈回归。采用工程原则，不照搬特定客户端或模型配置。

| skill | 职责 |
|---|---|
| `architect` | 调用方式、类型、状态归属、模块边界与迁移设计 |
| `session` | 暂停、交接与按证据恢复任务 |
| `evaluate` | 隔离执行技能任务，检查产物和工具记录，由独立者判定 |
| `mode` | 入口，选 playbook 并按步骤调用其他 skill |
| `brainstorm` | 需求追问 |
| `spec` | 生成 spec 并发布为 GitHub issue |
| `tickets` | 拆成可独立执行的 ticket |
| `implement` | 测试先行地实现并 commit |
| `diagnosing-bugs` | 复现、定位并修复 bug |
| `accept` | 非作者 agent 运行验收并审查改动的代码质量 |
| `pr` | push 分支、创建或更新 PR，并跟进当前 HEAD 的 CI |
| `create-verify-app` | 为项目生成 verify-app 类 skill |
| `codebase` | 把项目的形状规则落成会失败的检查，接进 CI，已有违规冻结成基线 |
| `codebase-audit` | 只读审计一块代码的结构问题，输出按修法组织的清单，每个修法标明能否配检查 |
| `setup` | 检查 gh 环境、账号和默认仓库，生成项目的验证 skill |
| `help` | 说明该用哪个 skill、怎么调用 |
| `skill-creator-plus` | 新建、修改和审查 skill |
| `prompt` | 编写和审查给 agent 读的文字 |
| `worktree` | 新建和清理项目内的 git worktree，把多个分支合并到集成 worktree，供其他 skill 读取 |
| `harness` | 通用说法在 Claude Code 和 Codex 中的对应操作，供其他 skill 读取 |
| `finish` | 独立验收、修复、PR/CI 和清理，供开发流程读取 |

## 开发

```bash
make test        # 校验结构、生成文件和确定性脚本测试
make regenerate  # 改了 VERSION 或 skills/ 后重新生成两端的清单和 Codex 镜像
```

版本号只改 `VERSION`。`.claude-plugin/`、`.agents/`、`plugins/jstack/` 都是生成的，不要手改。仓库结构、开发和发布规则见 `AGENTS.md`。

## 行为验证

本次证据与具体边界见 [2.2.0 验证记录](docs/validation-2.2.md)。

工作流改动用 [evaluate](skills/evaluate/SKILL.md) 执行隔离任务；运行方式见该 skill。自动检查只输出 FAIL、BLOCKED 或 NEEDS_REVIEW，PASS 需要非作者依据真实产物和工具记录判定。源码加载、已安装插件触发和跨客户端实测分别记录，不互相替代。

## 按需流程

- 跨模块契约、领域模型或旧 API 迁移：implement 先调用 architect；高风险设计按可用渠道引入独立观点。
- 反复出现的错误：maintenance 先尝试结构消除和类型约束，再立检查；修复与基线收紧同批完成。
- 验证材料维护：create-verify-app 逐功能核对源码与实际操作，区分文档漂移、工具缺口和产品回归。
- 性能与视觉任务：mode 分别选择 perf、visual，使用测量或浏览器证据。
- 长任务中断：session 保存目标、Git 状态、证据与剩余事项，恢复时只重跑失效证据。
- PR：只读脚本核对当前 HEAD、CI、review 和独立验收；本次明确要求合并时锁定 HEAD 并读回合并结果。
