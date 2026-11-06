# issue 状态

jstack 不用标签，issue 的状态全部用 GitHub 自带的功能表达。只有 j-mode 修改状态，implement 和 accept 只读 issue。

| 状态 | 表达方式 |
|---|---|
| 待实现 | open，没有 assignee |
| 被阻塞 | 原生 dependency，GitHub 自动显示 Blocked |
| 实现中 | open，assignee 为当前 gh 账号 |
| 验收失败 | open，有 assignee，最新评论是 FAIL 结论 |
| 待人工验收 | open，有 assignee，最新评论是 PASS+NOTES，并列出受阻的检查 |
| 完成 | closed，原因 completed，关闭前已评论 accept 结论 |

spec 和 ticket 靠父子关系区分：有父 issue 的是 ticket，挂着子 issue 的是 spec。

## 命令

```bash
# 开始一张 ticket
gh issue edit <编号> --add-assignee @me

# 贴 accept 结论（正文先写进 f=$(mktemp)）
gh issue comment <编号> --body-file "$f"

# 结论为 PASS，或 PASS+NOTES 且没有受阻项
gh issue close <编号> --reason completed

# spec 下的 ticket 是否全部关闭
gh api repos/<owner>/<repo>/issues/<spec 编号>/sub_issues --jq '[.[] | select(.state == "open")] | length'

# 查一张 ticket 被哪些 issue 阻塞（与 j-mode 记录的已合并 ticket 对照）
gh issue view <编号> --json blockedBy --jq '.blockedBy.nodes'

# 全部关闭后关闭 spec
gh issue close <spec 编号> --reason completed
```
