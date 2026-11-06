# 检查项说明

`scripts/check_env.py` 每行输出一个检查项，格式是 `<检查项>=<结果>`，最后一行是 `result=`。

| 检查项 | 结果 | 含义 | 必需 |
|---|---|---|---|
| `git` | `ok` / `missing` | git 是否在 PATH 中 | 是 |
| `gh` | `ok` / `missing` | gh 是否在 PATH 中 | 是 |
| `gh_auth` | `ok` / `not_logged_in` | `gh auth status` 是否成功 | 是 |
| `gh_features` | `ok` / `missing <参数>` | `gh issue create --help` 是否列出 `--blocked-by` 和 `--parent` | 是 |
| `github_remote` | `owner/repo` / `none` | `git remote -v` 中第一个 GitHub 仓库 | 是 |
| `labels` | `ok` / `missing <标签>` / `unknown` | 仓库是否已有 `jstack:spec`、`jstack:ticket` | 否，步骤 4 补齐 |
| `agents_md` | `absent` / `no_jstack_block` / `has_jstack_block` | `AGENTS.md` 是否存在，是否已有 `## jstack` 块 | 否，步骤 4 写入 |
| `claude_md` | `absent` / `missing_import` / `imports_agents` | `CLAUDE.md` 是否存在，是否引用了 `@AGENTS.md` | 否，步骤 5 提示 |

`result=ok` 表示所有必需项都满足。`result=blocked <检查项>` 列出未满足的必需项，此时退出码为 1。

## 安装命令

| 平台 | git | gh |
|---|---|---|
| macOS（Homebrew） | `brew install git` | `brew install gh` |
| Debian / Ubuntu | `sudo apt install git` | 见 https://github.com/cli/cli/blob/trunk/docs/install_linux.md |
| Windows（winget） | `winget install Git.Git` | `winget install GitHub.cli` |

升级 gh：macOS 用 `brew upgrade gh`，Windows 用 `winget upgrade GitHub.cli`。

## 创建标签

```bash
gh label create "jstack:spec" --repo <owner/repo> --description "jstack 生成的 spec" --color 0E8A16
gh label create "jstack:ticket" --repo <owner/repo> --description "jstack 生成的 ticket" --color 1D76DB
```

只创建 `labels` 中列为缺少的标签。
