# 检查项说明

`scripts/check_env.py` 每行输出一个检查项，格式是 `<检查项>=<结果>`，最后一行是 `result=`。

| 检查项 | 结果 | 含义 | 必需 |
|---|---|---|---|
| `git` | `ok` / `missing` | git 是否在 PATH 中 | 是 |
| `gh` | `ok` / `missing` | gh 是否在 PATH 中 | 是 |
| `gh_auth` | `ok` / `not_logged_in` | `gh auth status` 是否成功 | 是 |
| `gh_features` | `ok` / `missing <参数>` | `gh issue create --help` 是否列出 `--blocked-by` 和 `--parent` | 是 |
| `github_remote` | `owner/repo`（多个时逗号分隔） / `none` | `git remote -v` 中的 GitHub 仓库 | 是 |
| `default_repo` | `owner/repo` / `unset` | 只在有多个 GitHub remote 时输出：`gh repo set-default` 是否已指定 | 是 |
| `gh_permission` | `ok` / `insufficient <权限>` | 当前活跃账号对仓库至少有 TRIAGE 权限 | 是 |

`result=ok` 表示所有必需项都满足。`result=blocked <检查项>` 列出未满足的必需项，此时退出码为 1。

## 安装命令（macOS）

```bash
brew install gh      # 安装
brew upgrade gh      # 升级
```
