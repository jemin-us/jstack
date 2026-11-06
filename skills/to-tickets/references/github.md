# GitHub 命令

在第 2 步读取 spec、第 6 步发布 ticket 时读取本文件。所有命令都在目标仓库的目录里运行，`gh` 会根据 `git remote` 自动识别仓库。

## 读取 spec

```bash
gh issue view <编号> --json number,title,body,labels,comments
```

## 发布一张 ticket

正文较长，先用 `f=$(mktemp)` 建一个系统临时文件写入正文（不放进项目目录），再用 `--body-file "$f"` 传入：

```bash
gh issue create \
  --title "<中文标题>" \
  --body-file <正文文件> \
  --label "jstack:ticket" \
  --parent <spec 编号> \
  --blocked-by <编号1>,<编号2>
```

- 没有阻塞时，去掉 `--blocked-by`。
- 命令输出新 issue 的链接，从中取出编号，供后面的 ticket 引用。

## 补救命令

发布失败后用这些命令补救：

```bash
gh issue list --label "jstack:ticket" --state open --json number,title
gh issue edit <编号> --parent <spec 编号>
gh issue edit <编号> --add-blocked-by <编号>
```

## 核对结果

```bash
gh issue view <spec 编号> --json number,title
gh issue list --label "jstack:ticket" --state open --json number,title
```

已在 gh 2.103.3 上核实 `--parent`、`--blocked-by`、`--add-blocked-by` 这三个参数。
