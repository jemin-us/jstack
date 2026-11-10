# skill 的调用与拆分

写的是 skill 时读本文件，决定调用方式和是否拆成多个 skill。其余写法见 [principles.md](principles.md)。

## 调用方式

两种选择，分别付出两种负担之一：

| | 自动调用 | 手动调用 |
|---|---|---|
| 谁能调用 | agent 自己判断后调用，其他 skill 也能调用；用户仍可手动输入名字 | 只有用户输入名字才能调用，其他 skill 不能调用 |
| 负担 | description 一直加载，占上下文 | 不占上下文，用户要自己记得它 |
| description 写法 | 写给模型看，列出触发分支 | 写给人看，一句话概括，不列触发词 |
| 设置 | Claude Code：不写 `disable-model-invocation`；Codex：`agents/openai.yaml` 中 `allow_implicit_invocation: true` | Claude Code：`disable-model-invocation: true`；Codex：`allow_implicit_invocation: false` |

只有当 agent 必须自己找到它、或另一个 skill 必须调用它时，才选自动调用。只靠手动触发的 skill 设为手动调用，不付上下文负担。

只放参考内容、被多个 skill 共用的自动调用 skill，可以作为共享参考的唯一出处。两个手动调用的 skill 需要共用的参考，两边都放不了，因为它们互相调不到，这时把参考放在 skill 体系之外的普通文件里，让两边都用指针指向它。

## 按调用方式拆分

有一个你在 prompt 里真会说的独立触发词，或者另一个 skill 必须调用它时，才把一块内容拆成单独的自动调用 skill。新 skill 的 description 会一直加载，所以单独触发必须值这个代价。

## 路由 skill

手动调用的 skill 多到记不住时，用一个手动调用的路由 skill 列出其他 skill 和各自的使用时机，用户只需记住这一个。路由 skill 只能提示，不能替用户触发其他手动调用的 skill。
