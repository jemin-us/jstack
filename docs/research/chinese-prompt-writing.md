# 中文指令写法调研

调研日期：2026-11-09。问题：用中文写给 agent 执行的指令（skill、`AGENTS.md`、`CLAUDE.md`、系统提示词）时，什么写法让模型执行得更稳定。方法：5 个检索角度，读取 20 个来源，抽出可证伪的论断，每条由 3 个独立 agent 反向核查，2 票反对即否决。

## 结论

实证只支持几条有限的结论。中文指令平均执行得比英文差，差距随模型变化；精确的字数、句数约束在中文下最不可靠；中文正文里夹英文术语无害。否定句、模糊量词（适当、尽量）、被动句、长句、术语不一致，没有找到中文专门的实证，目前都是经验之谈。结构化写法（分隔符、编号步骤、写明输出语言）只有厂商建议，没有中文对照实验。

## 证据

| 结论 | 置信度 | 依据 |
|---|---|---|
| 多数模型执行中文指令弱于英文，差距因模型而异 | 高 | Multi-IF 中 14 个模型有 13 个中文低于英文（GPT-4o 第 1 轮 0.805 对 0.874）；XIFBench 中 Claude-3.5-Sonnet 66.1→53.0，GPT-4o 76.9→73.3；SWE-bench Lite 50 例预印本中，人工翻译的中文任务描述使 3 个模型解决率下降 4.5–9.9pp。来源：[Multi-IF](https://arxiv.org/html/2410.15553v2)、[XIFBench](https://arxiv.org/html/2503.07539v2)、[arXiv 2604.14210](https://arxiv.org/pdf/2604.14210) |
| 原生中文指令评测远未饱和，中文弱的模型差得多 | 中 | CIF-Bench 28 个模型最高 52.9%；CFBench 全集 GPT-4o 0.735、Hard 集 0.582，Mistral-7B 仅 0.054。来源：[CIF-Bench](https://arxiv.org/pdf/2402.13109)、[CFBench](https://arxiv.org/html/2408.01122v2) |
| 精确字数、句数、词汇约束最不可靠，中文下普遍超长 | 高 | CFBench 所有模型在词数、句数约束上都差；LIFEBench 26 个模型几乎都在中文上更差，多数超额生成。中文按字、英文按词计长也可能贡献部分偏差。来源：[CFBench](https://arxiv.org/html/2408.01122v2)、[LIFEBench](https://arxiv.org/pdf/2505.16234) |
| 改用英文写提示不一定更好 | 低 | 微调模板实验中 LLaMA 用中文更好、Bloom 用英文更好，差距 1–1.4 分，且是训练期结果；Claude 当前模型 Global-MMLU 中文为英文的 97.7%–99.3%，属知识问答。来源：[arXiv 2310.07328](https://arxiv.org/pdf/2310.07328)、[Anthropic 多语言文档](https://platform.claude.com/docs/en/build-with-claude/multilingual-support) |
| "中文省 token"不成立，随模型变化 | 低 | agentic 编码中中文与英文 prompt token 之比：MiniMax-2.7 1.28、GPT-5.4-mini 1.09、GLM-5 0.98；单篇预印本、3 个模型、50 例。来源：[arXiv 2604.14210](https://arxiv.org/pdf/2604.14210) |
| 中文正文夹英文术语无害，英文正文夹中文略降 | 中 | 替换约 30% 名词：中文夹英文持平或略升，英文夹中文 8 个模型全部下降；测的是理解任务，最大 72B。来源：[ACL 2026](https://aclanthology.org/2026.acl-long.2080.pdf) |
| 在系统提示词中写明输入和输出语言 | 中 | 厂商建议，无量化数据。来源：[Anthropic 多语言文档](https://platform.claude.com/docs/en/build-with-claude/multilingual-support) |
| 用分隔符区分输入、把任务拆成编号步骤 | 低 | 厂商建议，内容与 OpenAI 指南一致，无实验。来源：[Kimi 指南](https://platform.kimi.ai/docs/guide/prompt-best-practice) |
| 提示格式（纯文本、Markdown、JSON、YAML）显著影响结果，小模型更敏感 | 低 | GPT-3.5 在代码翻译上最多差 40%，GPT-4 更稳；英文提示、旧模型。来源：[arXiv 2411.10541](https://arxiv.org/abs/2411.10541) |
| 禁令配上相关干扰文本可能反而带出被禁内容 | 低 | ReboundBench 约 5,000 条英文提示、9 个开源模型，测对数概率；最大模型几乎无反弹。来源：[arXiv 2511.12381](https://arxiv.org/pdf/2511.12381v1) |

置信度规则：多个一手来源且核查一致为高；单篇同行评审或厂商建议为中；预印本、经验建议或需要较大外推为低。

## 被否决的论断

| 论断 | 票数 |
|---|---|
| 中文训练充分的模型（GLM-4-9B、Qwen-2.5-72B）说明差距取决于模型训练 | 1-2 |
| 跨语言时格式和数值约束最稳定，宜把要求写成数值约束 | 0-3（与 CFBench 数值约束结果矛盾） |
| 原生中文新编任务比英文直译任务低 2.2% | 0-3 |

## 注意

- 多数基准测的是 2023–2025 年初的模型，前沿模型的中英差距缺少独立的指令遵循数据。
- Multi-IF、XIFBench 的中文数据译自英文，差距中有一部分来自翻译。
- token 成本和 SWE-bench 两条来自同一篇小样本预印本；否定句研究只有英文小模型。

## 待核实

- 模糊量词、被动句、长句、术语不一致对指令遵循的量化影响。
- 前沿模型上同一份 agent 指令中英两版在真实 agentic 任务上的差距。
- 编号步骤、完成标准、XML 标签、示例在中文提示中的增益是否与英文相同。
- 通义、DeepSeek、智谱官方指南中针对中文的写作建议。
