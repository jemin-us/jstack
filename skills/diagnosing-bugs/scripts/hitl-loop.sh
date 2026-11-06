#!/usr/bin/env bash
# 人工协助复现脚本。复制本文件，改写下方步骤后运行。
# agent 运行脚本，人在终端里按提示操作；结束时以 KEY=VALUE 输出结果供 agent 解析。
# 只收集观察结果；登录这类操作写成 step，交给人完成，不要用 capture 收集凭据。
set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [完成后按回车] " _
}

capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question"
  read -r -p "    > " answer
  printf -v "$var" '%s' "$answer"
}

# --- 从这里开始改写 ---

step "打开 http://localhost:3000 并登录。"
capture ERRORED "点击“导出”按钮，是否报错？(y/n)"
capture ERROR_MSG "粘贴报错信息（没有就填 none）："

# --- 改写到这里为止 ---

printf '\n--- 结果 ---\n'
printf 'ERRORED=%s\n' "$ERRORED"
printf 'ERROR_MSG=%s\n' "$ERROR_MSG"
