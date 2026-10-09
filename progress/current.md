# 当前状态

更新日期：2026-10-09。

最新工作会话：`6f2792f5-802a-49a7-a376-78c1abd74ffa`。讨论经过与原始对话定位见[会话记录](2026-10-08-research-skills.md)。

## 目标与已确定的边界

AutoResearch 是 Claude Code plugin，包含 `research-mode` 导航入口和 15 个简短 leaf skills。每个 leaf 只做一个认知变换。保持 leaf 最小化，入口提供可用的路由关系。hooks 尚未实现。

实际使用目标是一次用户请求启动 `/autoresearch:research-mode`，agent 自己选操作、调用 skills 并完成原始任务。中间无需用户逐步确认，不固定 leaf 顺序或调用次数，不靠脚本追加用户消息救回未完成任务。

实验比较实际使用效果，允许技能组使用额外步骤，同时记录 token 和时间。质量提升和最终任务交付分别检查。

## 最新接入约定与运行

2026-10-09 用户明确要求保留 benchmark 的 instruction、input 和 output，只接入通用研究 agent。约定见[接入文档](../docs/agent-benchmark-contract.md)，通用说明见[research agent](../docs/research-agent.md)。移除 runner 的 hypothesis 包装，不修改 15 个 leaf。AI Idea 的新三题对比已完成，9/9 份七字段 idea 与 27/27 次有效最终评分均已核验。Direct、Reflection、Skills 动机相似度分别为 3.33、3.00、3.33，实验相似度为 3.67、3.33、3.33，主题对齐均为 5。Skills 入口被识别但研究 leaf 调用为零，没有展示质量提升。本轮使用本地全文任务接口，与作者预处理摘要不同。详见[本轮进度](2026-10-09-ai-idea-rerun.md)和[完整报告](../results/ai-idea-official-task-20261009T072408Z/report.md)。

## 当前入口版本

插件当前版本为 0.1.1。[research-mode](../skills/research-mode/SKILL.md)现在要求根据研究状态选择最小有用操作，通过 `Skill` 工具加载所选 leaf，按其指令执行，再把结果用于后续操作和原任务交付。没有固定技能序列或次数，也不要求中间确认。15 个 leaf 保持不变，通用 agent 说明同步明确选中操作后的加载规则。

这次变更参考了 ask-matt 的技能导航与 poteto-mode 的执行触发规则。它针对 AI Idea 重跑中零 leaf 调用暴露的执行关系缺口，但零调用的具体原因尚未确定。新规则只完成本地结构校验，尚未做模型复测，不能宣称已解决零调用或提高质量。详见[变更记录](2026-10-09-router-and-repository.md)。

下文所有实验都使用历史入口。ResearchBench 第四题复测、其他五项 benchmark 及 AI Idea 接入纠正后的重跑使用前一版自主完成规则；ResearchBench 的 12 题全量对比使用更早版本。不要将历史结果归到当前 0.1.1。

## 实验状态

数据来自 ResearchBench tiny 的 12 个研究问题和参考摘要。候选模型使用 TokenDance MiMo-V2.6-Flash；盲评使用 Ling-3.1-Flash。匹配分是与隐藏目标方法要点的重合度，不能证明创新性或科研成功。

| 轮次 | Direct 匹配均分 | Reflection 匹配均分 | Skills 匹配均分 | 主要结论 |
| --- | ---: | ---: | ---: | --- |
| 首轮单次 API prompt 对照 | 3.167 | 3.750 | 3.167 | 完整 suite prompt 未显示优势；没有测原生路由 |
| 首轮全原生 Claude Code | 未完整评分，范围 3.17–3.58 | 3.250 | 3.500 | Skills 交付 11/12，note05 停在机制笔记 |
| 上一版入口全量重跑 | 3.167 | 3.333 | 3.417 | Skills 仍交付 11/12，note04 停下来等待确认 |

上一版入口全量重跑共 36 次候选生成和 36 条有效评分，Skills 的 32 次调用全部成功。Direct、Reflection 和 Skills 的字数合规分别为 12/12、12/12、9/12。note11、note12 虽有最终假设，却混入中间笔记。将未交付的 note04 按零分作独立本地分析后，Skills 均分为 3.167。该分析不是官方匹配评分。

这些小样本实验没有支持稳定的 Skills 质量优势。具体方法、用量、逐题结果和限制见[实验说明](../docs/experiments.md)及[上一版全量报告](../results/runtime-revised-20261008T122704Z/report.md)。

## 最新单题复测

用户要求替换入口完成规则，并快速重跑 note04 一次。

- 相同任务提示、模型、protocol 和 15 个 leaf；仅入口完成句改变。
- 一次原生用户请求，agent 自主执行 `reconstruct → assumption-map → boundary-push → prediction`。
- 最终交付 114 词的假设正文，没有请求确认，也没有附上中间笔记。
- 回复附有简短标题，runner 连标题计为 119 词。字数合规，严格的仅正文格式仍有偏差。
- 耗时 258.2 秒；没有新增 judge 调用。

[单题报告](../results/autonomy-check-20261008T132400Z/report.md)、[最终输出](../results/autonomy-check-20261008T132400Z/main/calls/note04/skill-prompt/output.txt)、[输入一致性检查](../results/autonomy-check-20261008T132400Z/input-verification.json)。

该次复测证明这一回合自主交付成功。它不能证明跨题稳定完成，也不能证明入口句的因果效果或答案质量提升。

## 当前解释与未解决问题

轨迹显示，未完成任务的 agent 已经知道下一步可以做什么，却在完成局部 leaf 后返回建议并等待用户。整体交付要求没有被可靠地延续到局部操作之后。这是有轨迹支持的解释，尚未确定是哪条措辞或哪个因素直接导致。

最新假设把声学微流控分离与 SPRi 检测组合起来，机制具体，但属于自然的方法组合。参考论文中的性能不能直接视为组合系统性能，培养液中的关联能否迁移到全血也仍需验证。这是人工内容分析，没有新增盲评分数。

仍需回答的问题包括当前规则的完成稳定性、最终输出格式，以及额外操作是否提高研究质量。进一步实验或修改尚未因这些问题而自动启动。

## 接续工作

先阅读本文件和会话记录，再按需要查看相应 `results/` 原始材料。

2026-10-09 用户授权快速并行跑另外五个 benchmark 的少量任务，比较 Direct、Reflection 和原生 Research skills。ResearchClawBench 使用 gpt-6.1-sol，其余使用 MiMo 2.6 Flash。初始范围为 54 次候选任务。四项文本生成已结束，共 51 次会话、50 次原生成功、1 次超时、32 次成功 leaf 调用；独立报告已写出。AI Idea 仅 6/27 条有效最终评分，AgentIdea 与 Forecast 无完整有效评分，Comparative 三组 both-orders-correct 均为 1/4。ResearchClaw 的两个 baseline 在 1000 秒超时，有正确表格和图，但缺最终报告。Skills 自行修复报告代码，在 997.95 秒完成，交付 6 个代码文件、完整报告与 7 张图，5 项有效 checklist 加权为 38.38/100。主会话独立核对全部 15 张核心表和真实产物。本轮 54 个候选已全部尝试，51 次原生成功、3 次超时、36 次成功 leaf 调用，不能据此声称稳定质量优势。见[本轮总报告](../results/multi-bench-20261008T163557Z/report.md)及[进度记录](2026-10-09-other-benchmarks.md)。

后续如继续验证，应保留单次请求、自主路由与自主停止的设计，分别审计最终交付和内容质量。保持 leaf 简短，避免用固定技能序列或外部补问掩盖提前停止。

仓库整理将插件、实验脚本、文档与进度保存到 Git。原始 `results/`、会话捕获、本机客户端配置、缓存和 `decisions.tsv` 留在本地并被忽略。历史实验没有因整理而重跑或修改。当前 0.1.1 的本地提交范围与验证记录见[仓库整理记录](2026-10-09-router-and-repository.md)。
