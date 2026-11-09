---
name: skill-creator-plus
description: 当任务涉及新建、修改或审查 skill，编写 SKILL.md，优化 description 或排查触发问题时使用。量化评测使用 skill-creator。
---

# Skill 创建与审查

## 硬性规则

违反以下任意一条，skill 会无法加载、不触发或触发错误：

- 主文件名必须是 `SKILL.md`，大小写一致。
- `name` 和文件夹名相同，使用 kebab-case，不包含 `claude` 或 `anthropic`。
- `description` 不超过 1024 字符，不包含 `<` 和 `>`。
- frontmatter 以 `---` 开头和结尾，内容是合法的 YAML。
- skill 文件夹内不放 `README.md`。说明文档放在仓库的文档目录中。

每次修改后运行校验：

```bash
python3 <本 skill 目录>/scripts/validate_skill.py <skill 目录>
```

## 语言规则

- 默认用简体中文书写，包括 description、正文、示例和 references。
- 只有以下英文保留原文：技术术语、产品名、代码标识符、命令、路径、文件名、错误信息。例如 skill、SKILL.md、MCP、Figma、PostgreSQL。
- 不写中英混排的句子，不在中文后面括注英文翻译，不用英文作章节标题。
- 用户指定其他语言时，按用户要求书写。

## 创建流程

### 1. 明确用例

确认 2–3 个具体用例，每个用例写清以下内容：

- 触发说法：用户会怎么说，至少 3 种。
- 执行步骤。
- 交付结果。

同时确认三件事：

- 需要哪些工具：内置工具、MCP 或脚本。
- 要内嵌哪些领域规则。
- 和哪些相邻 skill 有边界。

用例说不清时，先追问用户，不要动笔。

### 2. 确定位置和结构

- 用户级 skill 放在 `$HOME/.claude/skills/<name>/`。
- 项目级 skill 放在 `<仓库>/.claude/skills/<name>/`。
- 写入已有的 skill 仓库前，先读仓库根 README 和同分类下现有的 skill，按它们的目录、文档、登记方式和版本号格式来做。详见 [references/repo-conventions.md](references/repo-conventions.md)。
- 子目录只建需要的：
  - `references/`：按需读取的细节。
  - `scripts/`：确定性的检查或处理。
  - `assets/`：模板和素材。

### 3. 编写 description

description 决定 skill 是否被加载，按以下句式书写：

```
当任务涉及 <关键词 1>、<关键词 2>、<关键词 3> 时使用。<相邻场景> 使用 <其他 skill>。
```

- 只写触发判断需要的关键词：用户常说的动作、对象、系统名、文件类型。
- 用相邻 skill 的名字标明边界，防止误触发。
- 不写实现细节、价值描述或修饰语。

正反例和字段说明见 [references/frontmatter-and-description.md](references/frontmatter-and-description.md)。

### 4. 编写正文

- 最关键的约束写在正文开头。
- 主流程用编号步骤写，每步写清动作和完成标准。
- 指令要能直接执行，写出命令、路径和判断条件。不写“确保质量”这类空话。
- 写明出错时怎么处理，按“现象、原因、处理”三项写。
- 给出 1–2 个示例：用户怎么说，skill 执行了哪些动作，得到什么结果。
- 正文只放主流程，细节放进 `references/`，并注明在什么情况下读哪个文件。
- 正文控制在 5000 词以内，越短越好。
- 格式、命名、必填项这类检查，写成 `scripts/` 中的脚本。

正文模板和常见写法见 [references/patterns.md](references/patterns.md)。

### 5. 校验和测试

1. 运行校验脚本，清除全部“错误”，逐条判断“提醒”。
2. 写触发测试：至少 5 条应触发的说法（包含换一种说法），至少 3 条不应触发的说法（包含相邻 skill 的典型说法）。
3. 选一个真实且有难度的任务跑通，同一任务跑 3 次，检查输出结构是否一致。

测试方法和排错见 [references/testing-and-troubleshooting.md](references/testing-and-troubleshooting.md)。

### 6. 交付

向用户说明以下内容：

- skill 路径和文件清单；
- 最终的 description；
- 触发测试的说法清单；
- 尚未验证的部分。

## 审查和改进流程

1. 运行校验脚本。
2. 按 [references/checklist.md](references/checklist.md) 逐项检查。
3. 逐句对照 [references/writing.md](references/writing.md)，列出违反的条目和所在行。
4. 定位问题：
   - 不触发或误触发：改 description。
   - 触发后不按指令执行：改正文，常见原因是过长、关键约束靠后、措辞含糊。
5. 列出问题和修改建议，每条建议说明它解决哪个问题。
6. 用户确认后再修改，修改后升级 `metadata.version`。
