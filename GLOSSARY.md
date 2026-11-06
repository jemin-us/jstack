# jstack

一套个人工程方法论，打包成同一个插件，供 Claude Code 和 Codex 两个 Harness 加载使用。参考 pstack 与 mattpocock skills。

## Language

**Harness**:
加载并运行插件的 agent 宿主，目前指 Claude Code 和 Codex。
_Avoid_: 平台、客户端、宿主

**Adapter**:
一份按 Harness 写的对照表，说明 jstack 正文里的通用说法在该 Harness 上对应什么工具或写法。
_Avoid_: shim、兼容层

**Brief**:
交给 subagent 的完整任务说明，以文件形式放在 skill 的 `references/` 下，由 Harness 自带的通用 agent 执行。
_Avoid_: agent 定义、custom agent

**验收检查**:
写在 ticket 里的一条可运行、能判定通过或失败的检查，格式为"命令或操作 → 期望结果"，由 to-tickets 生成。
_Avoid_: 验收谓词、验收标准、DoD、checklist

**Playbook**:
针对一类任务的固定执行步骤，由 j-mode 选中后逐步执行，每一步都写明完成标准。
_Avoid_: 工作流模板、recipe

**Skill**:
一个遵循 Agent Skills 标准的目录，以 `SKILL.md` 为入口，是插件里最小的可复用单元。
_Avoid_: 技能包、prompt
