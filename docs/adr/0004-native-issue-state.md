# issue 状态只用 GitHub 原生功能，不用标签

jstack 不创建也不使用任何标签。issue 的状态全部用 GitHub 自带的功能表达：open/closed 表示是否完成，assignee 表示正在实现，原生 dependency 表示被阻塞，评论记录 accept 结论，父子 issue 关系区分 spec 和 ticket。原先的 `jstack:spec`、`jstack:ticket` 标签只能区分类型，看不出状态，而补齐状态标签又要在每个仓库里建标签、在流程中不断同步。只有 j-mode 修改 issue 状态，implement 和 accept 只读。

## Consequences

"验收失败"和"待人工验收"在 issue 列表里无法直接筛选，要看最新一条评论才能区分；j-mode 收尾时会列出这两类 issue。
