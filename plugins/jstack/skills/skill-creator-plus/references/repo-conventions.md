# 写入已有 skill 仓库

## 通用步骤

1. 读仓库根目录的 README，确认分类方式和登记规则。
2. 读同分类下 1–2 个现有 skill，记下以下约定：
   - description 句式
   - `metadata.version` 的格式
   - 子目录结构
   - 是否附带其他工具的配置
3. 按这些约定新建或修改 skill。

## ai-skills 仓库约定

约定发生变化时，以仓库内的实际文件为准。

| 项目 | 约定 |
|---|---|
| 源码位置 | `<分类>/<分类>-<技能>/`，例如 `shop4/shop4-web-development/` |
| description | `当……时使用。` 句式；有相邻 skill 时补一句“……使用 <skill 名>。” |
| 版本号 | `metadata.version` 写成带引号的字符串，例如 `"1.0.0"`；每次修改都升级 |
| 给人看的文档 | 放在 `<分类>/docs/<技能>.md`，不放进 skill 文件夹 |
| 登记 | 新 skill 登记到 `<分类>/README.md`；新分类登记到根目录 `README.md` |
| Codex 配置 | 同分类的 skill 带有 `agents/openai.yaml` 时，新 skill 也补上，填写 `display_name`、`short_description` 和 `default_prompt` |

## jstack 仓库约定

仓库：`jemin-us/jstack`。约定发生变化时，以仓库内的实际文件为准。

| 项目 | 约定 |
|---|---|
| 源码位置 | `skills/<技能>/` |
| 调用方式 | 默认自动调用。两处设置保持一致：SKILL.md 不写 `disable-model-invocation: true`，`agents/openai.yaml` 写 `allow_implicit_invocation: true`；改成手动调用时两处同时改。只供其他 skill 读取的 skill（`worktree`、`harness`、`finish`）设为手动调用 |
| 跨 skill 引用 | 只链接其他 skill 的 `SKILL.md`，不链接它的 `references/`、`scripts/`；两个以上 skill 共用的内容抽成单独的 skill |
| Codex 配置 | 每个 skill 都带 `agents/openai.yaml`，填写 `display_name`、`short_description` 和 `policy.allow_implicit_invocation` |
| 校验 | 在仓库根目录运行 `python3 scripts/validate.py`，结果为“通过” |
| 版本号 | 改动 `skills/` 时，递增根目录 `VERSION`，再运行 `make regenerate`；skill 自身不写 `metadata.version` |
| 登记 | 新 skill 登记到根目录 `README.md` 的 skill 表和 `help` 的"地图" |
