#!/bin/sh
# 在主目录运行：清理失效的 worktree 记录，把两个 worktree 目录写进本地排除文件，列出已有的 jstack worktree。
git worktree prune || exit 1
f="$(git rev-parse --git-common-dir)/info/exclude" || exit 1
mkdir -p "$(dirname "$f")"
if [ -s "$f" ] && [ -n "$(tail -c1 "$f")" ]; then echo >> "$f"; fi
for p in .claude/worktrees/ .codex/worktrees/; do
  grep -qxF "$p" "$f" 2>/dev/null || echo "$p" >> "$f"
done
git worktree list | grep -e '/.claude/worktrees/' -e '/.codex/worktrees/' || true
