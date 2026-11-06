---
name: create-verify-app
description: 当任务涉及为项目生成或更新 verify-app 类 skill、让 agent 像用户一样启动和操作 app 并留下证据时使用。执行一张 ticket 的验收使用 accept。
disable-model-invocation: true
---

# 生成项目验证 skill

在目标项目里生成一个项目本地的 `verify-<app>` skill。它写明怎样启动这个 app、怎样像用户一样操作它、证据放在哪里。读它的是之后的 agent，往往是执行 accept 的 agent，而且没见过这个 app。所以每一步都要写成能直接照做的命令。

## 硬性规则

- 关键：生成之后必须按它亲自跑一遍，Launch、Doctor、Drive、Evidence、Cleanup 全部跑通，并且确认 Cleanup 之后证据还在。没跑通过的 skill 只是草稿，不能交付。
- 不许为了让流程跑通而放宽操作路径。预置数据缺了某个前提，就把这条路径记为失败，原因写进该功能的"注意事项"，不要改步骤绕过去。
- 实体文件放在 `.agents/skills/verify-<app>/`，再建 symlink `.claude/skills/verify-<app>` 指向它。不要在两处各放一份副本。
- 项目里已经有 verify 类 skill 时，在原有基础上更新，不另建一个。
- 命令、选择器、路由必须取自这个仓库的真实内容。生成物里不能留占位符。
- Cleanup 只结束本次运行启动的进程，不按进程名去杀进程，也不删除证据。

## 流程

### 1. 检查是否已有 verify skill

```bash
ls -d .agents/skills/verify-* .claude/skills/verify-* 2>/dev/null
```

找到了：读出它的内容，后面按"更新"处理，保留其中仍然正确的步骤和功能清单。
没找到：按"新建"处理，`<app>` 取项目名，用 kebab-case，例如 `verify-shop4-web`。

完成标准：确定是新建还是更新，并确定 skill 名。

### 2. 探测项目

先从仓库里找答案，只有仓库里看不出来的才向用户提问。逐项弄清：

- **使用面**：用户实际接触的是什么，例如 Web 界面、CLI、桌面应用、API。有多个时以最主要的一个为准，其余的记下来。
- **启动**：README、`package.json` 的 scripts、Makefile 里写的开发启动命令；端口、环境变量、预置数据、登录方式。
- **操作工具**：优先用仓库已有的工具，比如 Playwright 或 Cypress 用例、curl 能直接访问的接口、调试端口。都没有时再选通用方案：Web 用当前 Harness 可用的浏览器控制工具，CLI 用 tmux 或伪终端，服务用 HTTP 请求。
- **测试框架**：已有的测试命令，以及测试数据从哪里来。
- **隔离**：能不能同时跑两个实例（端口、数据目录是否冲突）。不能的话，要在生成物里写明"不要操作不是本次启动的实例"。

再按 README 里的命令实际启动一次。

完成标准：上面每一项都有答案，并且 app 在本机启动成功。

### 3. 生成 skill

按 [references/skill-template.md](references/skill-template.md) 生成以下文件：

- `.agents/skills/verify-<app>/SKILL.md`：包含 Launch、Doctor、Drive、Evidence、Cleanup 五段。
- `.agents/skills/verify-<app>/agents/openai.yaml`：设置 `allow_implicit_invocation: false`。
- `.agents/skills/verify-<app>/scripts/`：只有确实需要辅助脚本时才建。脚本要可执行，调用方式写进正文。

然后建 symlink：

```bash
mkdir -p .claude/skills
ln -s ../../.agents/skills/verify-<app> .claude/skills/verify-<app>
```

检查项目的 `.gitignore`，没有 `.verify-evidence/` 这一行就追加。

完成标准：`ls .claude/skills/verify-<app>/SKILL.md` 能读到文件；frontmatter 里有 `name`、`description`、`disable-model-invocation: true`；`.gitignore` 包含 `.verify-evidence/`。

### 4. 建功能清单

按 [references/feature-map.md](references/feature-map.md)，在 `features/` 下建一份索引，再为最主要的 3 到 5 个用户功能各写一个文件。功能从路由、命令、菜单和文档里找。每个文件都要写清楚：用户从哪些入口进入、每一步的操作命令和可观察的结果、怎样证明这个功能是好的。

完成标准：索引列出全部功能文件，每个功能文件都有固定的四个小节，且没有占位符。

### 5. 亲自跑一遍

按生成的 skill 从头执行：

1. Launch，等到"可用"信号出现。
2. Doctor，确认结果通过。
3. Drive，挑功能清单里的一个功能，走完它的全部步骤。
4. Evidence，把证据存到 skill 指定的位置。
5. Cleanup。
6. 再列一次证据目录，确认证据还在。

任何一步失败，先跑 Cleanup，再修改生成物，然后从第 1 步重新跑。如果是在替代环境里验证的（例如用本地栈代替远程环境），列出替代环境做了、真实环境不会做的步骤，并把这些步骤标为"未验证"。

完成标准：6 步全部通过，并贴出证据路径和 Doctor 的输出。

### 6. 交付

向用户说明以下几点：

- skill 路径、symlink 路径和文件清单；
- 第 5 步实际跑的是哪个功能，证据放在哪里；
- 证据目录 `.verify-evidence/` 已加入 `.gitignore`；
- 未验证的部分。

## 示例

用户说："给这个项目生成一个验证 skill。"

执行过程：

1. 没找到已有的 verify skill。
2. 探测到这是一个 Next.js Web 应用，启动命令 `pnpm dev`，端口 3000，仓库里有 Playwright。
3. 生成 `.agents/skills/verify-shop4-web/`，并建好 symlink。
4. 功能清单写了"登录""商品列表""下单"三个功能。
5. 按生成的 skill 亲自跑通"登录"，证据存在 `.verify-evidence/login/`，Cleanup 之后这些证据仍然存在。

结果：交付 skill 路径和证据路径，`.gitignore` 已包含 `.verify-evidence/`。

## 常见问题

现象：执行 `ln -s` 报 `File exists`。
原因：`.claude/skills/verify-<app>` 已经是一个真实目录，不是 symlink。
处理：对比它和 `.agents/skills/verify-<app>` 的内容，把差异合并进实体目录，再向用户确认能否删掉旧目录，然后重建 symlink。

现象：按 README 的命令启动后，app 不可用。
原因：仓库本身跑不起来，比如依赖没装、迁移没执行、缺少某个配置文件。
处理：先修好或准确报告问题，再生成 skill。有些缺失的东西和验证本身无关，但会挡住启动，比如一份示例配置。这类东西可以由生成的 skill 补上，标注为"验证用临时文件"，并在 Cleanup 里删除。

现象：Cleanup 之后证据不见了。
原因：证据目录放在了 Cleanup 会删除的临时目录里。
处理：把证据目录移到项目里的固定位置，例如 `.verify-evidence/`，然后从第 5 步重跑。

现象：找不到能操作这个使用面的工具。
原因：当前 Harness 没有浏览器控制工具，仓库里也没有可用的测试工具。
处理：向用户说明缺少什么工具，给出建议的安装方式，例如在项目里加 Playwright，等用户确认后再继续。不要改用静态检查来冒充操作验证。
