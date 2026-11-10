---
name: skill-creator-plus
description: 当任务涉及新建、修改或审查 skill，编写 SKILL.md，优化 description 或排查触发问题时使用。按用例确定结构，编写 description 和正文，运行校验脚本并做触发测试。量化评测使用 skill-creator。
---

# Skill 创建与审查

## 硬性规则

- 每次修改 skill 后运行校验脚本，清除全部"错误"，逐条判断"提醒"。文件名、`name`、frontmatter 格式、description 长度、`README.md` 和链接是否存在都由它检查：

  ```bash
  python3 <本 skill 目录>/scripts/validate_skill.py <skill 目录>
  ```

- 默认用简体中文书写；用户指定其他语言时按用户要求。
- 写入已有的 skill 仓库前，按 [references/repo-conventions.md](references/repo-conventions.md) 读仓库约定并照做。
- `references/` 没有覆盖的情况，或者用户要求对照官方规范时，读取 [assets/skill-build.pdf](assets/skill-build.pdf)。它和本 skill 不一致时以本 skill 为准：PDF 建议重复关键点、加强调标题和鼓励语，本 skill 要求一个约束只写一处。它共 33 页，按页码范围分段读取：技术要求在 10–13 页，测试在 15–17 页，常见写法和排错在 22–27 页，检查清单在 30–31 页。

## 创建流程

### 1. 明确用例

确认 2–3 个具体用例，每个用例写清三项：

- 触发说法：用户会怎么说，至少 3 种。
- 执行步骤。
- 交付结果。

再确认需要哪些工具（内置工具、MCP 或脚本）、和哪些相邻 skill 有边界。

然后不带 skill 把其中一个用例实际跑一次，记下模型做错的地方和缺少的上下文。skill 只写补上这些缺口的内容，模型不用提醒就能做对的不写。

完成标准：每个用例的三项都已写出，写不出时已向用户追问；有一份不带 skill 运行得到的缺口清单。

### 2. 确定位置和结构

- 用户级 skill 放在 `$HOME/.claude/skills/<name>/`，项目级 skill 放在 `<仓库>/.claude/skills/<name>/`。
- 子目录只建用得上的：`references/` 放部分分支才读的细节，`scripts/` 放确定性的检查或处理，`assets/` 放模板和素材。
- 决定自动调用还是手动调用。只被用户点名、或只被其他 skill 按路径读取的 skill 设为手动调用。

完成标准：skill 路径、子目录和调用方式都已确定。

### 3. 编写 description

按以下句式写：

```
当任务涉及 <关键词 1>、<关键词 2>、<关键词 3> 时使用。<做什么，一句话>。<相邻场景> 使用 <其他 skill>。
```

- 触发句：只写触发判断需要的关键词，取自用户的原话，包括动作、对象、系统名、文件类型。
- 做什么：主要动作和交付结果，不写内部实现方式、价值描述或修饰语。
- 边界：用相邻 skill 的名字标明，防止误触发。
- 手动调用的 skill 不靠 description 触发，改为先写做什么，再写由谁在什么时候读取。

字段规则和正反例见 [references/frontmatter-and-description.md](references/frontmatter-and-description.md)，拿不准某个字段或某种写法时读取。

完成标准：description 包含触发句和做什么；有相邻 skill 时包含边界。

### 4. 编写正文

按 [references/patterns.md](references/patterns.md) 的模板搭出章节，句子的写法读取 [writing-for-agents](../writing-for-agents/SKILL.md) 并照做。skill 另有五条结构规则：

- 一个约束只写一处，写在执行它的那一步。"硬性规则"只放不属于任何单一步骤的约束。
- 每步以完成标准结尾。完成标准写做完后的状态，不把步骤里的指令再说一遍。
- 示例和常见问题只写步骤里没有的信息：示例给一次从用户说法到结果的完整过程，常见问题给具体的报错和处理。流程类 skill 两者都要有；只放参考内容的 skill 写不出新信息时不写。
- 按步骤出错的代价定具体程度：做错代价高、必须按固定顺序的操作，给出原样执行的命令；有多种可行做法的判断，只给目标和判断条件。需要选工具或方案时给一个默认做法和换用的条件，不罗列选项。
- 格式、命名、必填项这类结果确定的检查，写成 `scripts/` 里的脚本，正文只写运行命令。

完成标准：正文里没有两处表达同一个约束；每步都有完成标准；每个 `references/` 文件都从 `SKILL.md` 直接链接，并有一句写明何时读取的指针。

### 5. 校验和测试

1. 写触发测试：至少 5 条应触发的说法（包含换一种说法），至少 3 条不应触发的说法（包含相邻 skill 的典型说法）。
2. 选一个真实且有难度的任务，同一任务跑 3 次。计划用在多个模型上时，每个模型都跑。

测试的写法和命令见 [references/testing-and-troubleshooting.md](references/testing-and-troubleshooting.md)。

完成标准：校验脚本没有"错误"；触发测试的每条说法都有结果；3 次运行的输出结构一致。没做的测试在交付时标"未验证"。

### 6. 交付

向用户说明：skill 路径和文件清单、最终的 description、触发测试的说法和结果、未验证的部分。

## 审查和改进流程

1. 按 [references/checklist.md](references/checklist.md) 逐项检查。
2. 读取 [writing-for-agents](../writing-for-agents/SKILL.md)，按它的审查任务逐句检查。
3. skill 不触发、误触发或触发后不按指令执行时，按 [references/testing-and-troubleshooting.md](references/testing-and-troubleshooting.md) 的"排错"表定位。
4. 按"条目、所在行、问题、改法"列出问题，用户确认后再修改。
5. 修改后按仓库约定升级版本号。

完成标准：清单的每一项都有结论；列出的每个问题都有所在行和改法。

## 示例

用户说："帮我建一个审查数据库迁移脚本的 skill。"

执行：追问出 2 个用例和各自的触发说法；确定为项目级、自动调用，建 `SKILL.md` 和 `references/`；写 description 和正文；校验脚本报"正文引用的文件不存在"，补上文件后通过；5 条应触发、3 条不应触发的说法逐条测试。

结果：交付 skill 路径和文件清单、最终的 description、触发测试的结果；功能测试只跑了 1 次，标为"未验证"。

## 常见问题

现象：校验脚本提醒 description 疑似中英混排。
原因：description 里有脚本词表之外的英文词。
处理：是术语、产品名或 skill 名就保留；是普通英文词就改成中文。
