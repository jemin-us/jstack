# skill 的调用与拆分

写的是 skill 时读本文件，决定调用方式和是否拆成多个 skill。其余写法见 [principles.md](principles.md)。

## 调用方式

两种选择，分别付出两种负担之一：

| | 自动调用 | 手动调用 |
|---|---|---|
| 谁能调用 | agent 自己判断后调用，其他 skill 也能调用；用户仍可手动输入名字 | 只有用户输入名字才能调用；其他 skill 不能通过 Harness 调用它，但可以按路径读取它的 `SKILL.md` |
| 负担 | description 一直加载，占上下文 | 不占上下文，用户要自己记得它 |
| description 写法 | 写给模型看，列出触发分支 | 写给人看，一句话概括，不列触发词 |
| 设置 | Claude Code：不写 `disable-model-invocation`；Codex：`agents/openai.yaml` 中 `allow_implicit_invocation: true` | Claude Code：`disable-model-invocation: true`；Codex：`allow_implicit_invocation: false` |

只有当 agent 必须自己找到它、或另一个 skill 只能通过 Harness 调用它时，才选自动调用。只靠手动触发、或只被其他 skill 按路径读取的 skill 设为手动调用，不付上下文负担。

多个 skill 共用的内容抽成一个单独的 skill，作为唯一出处；其他 skill 只引用它的 `SKILL.md`，不引用别的 skill 的内部文件。调用方按路径读取它时，把它设为手动调用，不付上下文负担；调用方只能通过 Harness 调用时，它必须是自动调用。

## 按调用方式拆分

有一个你在 prompt 里真会说的独立触发词时，才把一块内容拆成单独的自动调用 skill。新 skill 的 description 会一直加载，所以单独触发必须值这个代价。两个以上 skill 共用的内容也拆成单独的 skill，按上一节决定它是自动调用还是手动调用。

## 路由 skill

手动调用的 skill 多到记不住时，用一个手动调用的路由 skill 列出其他 skill 和各自的使用时机，用户只需记住这一个。路由 skill 只能提示，不能替用户触发其他手动调用的 skill。
