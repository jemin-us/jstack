# jstack

一套个人工程方法论，打包成同一个插件，供 Claude Code 和 Codex 两个 Harness 加载使用。

## Language

**Harness**:
加载并运行插件的 agent 宿主，目前指 Claude Code 和 Codex。
_Avoid_: 平台、客户端、宿主

**Adapter**:
一份按 Harness 写的对照表，说明 jstack 正文里的通用说法在该 Harness 上对应什么工具或写法。
_Avoid_: shim、兼容层

**自动执行**:
mode 发起的流程所处的状态：被读取的 skill 跳过发布 spec、发布 ticket、push 前的用户确认，brainstorm 只问一轮难以回头的决定。用户单独调用这些 skill 时不处于自动执行。
_Avoid_: 无人值守、全自动、autopilot

**Brief**:
交给 subagent 的完整任务说明，以文件形式放在 skill 的 `references/` 下，由 Harness 自带的通用 agent 执行。
_Avoid_: agent 定义、custom agent

**验收检查**:
写在 ticket 里的一条可运行、能判定通过或失败的检查，格式为"命令或操作 → 期望结果"，由 to-tickets 生成。
_Avoid_: 验收谓词、验收标准、DoD、checklist

**形状规则**:
项目对代码结构的一条约束，例如依赖方向、分层、命名、文件位置，由 codebase 落成检查。
_Avoid_: 架构规范、编码规范、最佳实践

**基线**:
立检查时已经存在的违规清单，检查只拦清单之外的违规，清单只减不增。
_Avoid_: 白名单、豁免清单、技术债列表

**结论**:
accept 对一次验收给出的判定，只有 PASS、PASS+NOTES、FAIL 三种。
_Avoid_: verdict、验收结果

**受阻**:
一条验收检查因为环境缺少条件（网络、浏览器、账号）而无法运行的状态，不等于通过。
_Avoid_: 跳过、skip

**测试接缝**:
测试观察行为的公开边界，测试只写在接缝上，不测内部实现。
_Avoid_: 测试点、seam

**验收范围**:
一次 accept 覆盖的 commit 范围，写作"起点..HEAD"，起点是实现开始前记下的 commit。
_Avoid_: diff 范围

**复现命令**:
能在某个 bug 上稳定失败的一条命令；修复后它就是这次修复的验收检查。
_Avoid_: repro、复现脚本

**集成分支**:
feature playbook 为一个 spec 建的分支 `jstack/spec-<编号>`，各 ticket 分支验收通过后合并到这里。
_Avoid_: 主分支、feature 分支

**波次**:
阻塞项都已完成、可以同时开工的一组 ticket，一波最多 3 张。
_Avoid_: 批次、wave

**Playbook**:
针对一类任务的固定执行步骤，由 mode 选中后逐步执行，每一步都写明完成标准。
_Avoid_: 工作流模板、recipe

**Skill**:
一个遵循 Agent Skills 标准的目录，以 `SKILL.md` 为入口，是插件里最小的可复用单元。
_Avoid_: 技能包、prompt
