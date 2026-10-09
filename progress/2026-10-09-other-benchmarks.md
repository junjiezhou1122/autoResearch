# 其他五项 benchmark 小样本对比

状态：本轮小样本任务已结束，五份报告与汇总已保存。更新日期：2026-10-09。

Session ID：`6f2792f5-802a-49a7-a376-78c1abd74ffa`。

本机原始对话：`/Users/junjie/.claude/projects/-Users-junjie-orca-projects-autoResearch/6f2792f5-802a-49a7-a376-78c1abd74ffa.jsonl`。

## 用户请求

用户要求把其他 benchmark 都跑少量 task，快速并行，通过干净的 `claude-research` agent 接入做简单比较。ResearchClawBench 必须用 `gpt-6.1-sol`，其他可以用 MiMo 2.6 Flash。完成后每个 benchmark 给一份报告，提供可用于改进 skills 的反馈。

## 初始范围

已有六个 benchmark，ResearchBench 已完成多轮实验，本次覆盖另外五个。

- AI Idea Bench：3 题 × Direct、Reflection、Skills。
- AgentIdeaBench：3 个子领域，各一个 idea × 三组。
- IdeaForecastBench：3 个任务 × 三组。
- Comparative Idea Evaluation：4 对方案 × 两个展示顺序 × 三组。
- ResearchClawBench：一个本机可执行任务 × 三组，执行环境与数据隔离先验证。

候选初始总数 54。每个 benchmark 独立工作目录，避免并行写共享文件。模型、输入与工具在同项三组间保持一致；技能组使用当前入口的自主完成规则，不改 leaf，不插入救援回合。

[计划与完成标准](../results/multi-bench-20261008T163557Z/plan.md)。

## 结果

四项文本任务已完成 51 个候选会话，50 次原生成功，1 次 Direct 超时。主会话独立核对全部 stream，成功 leaf 调用共 32 次。四份报告已写入各 benchmark 目录。不同 benchmark 的分数不合并。

- [AI Idea Bench 报告](../results/multi-bench-20261008T163557Z/ai-idea-bench/report.md)。9 次生成完成，Skills 严格格式 0/3。评分器曾从 reasoning_content 恢复分数，已撤回完整均分；仅 6/27 条最终 content 评分有效。
- [AgentIdeaBench 报告](../results/multi-bench-20261008T163557Z/agent-idea-bench/report.md)。9 条假设交付。官方检索与 critic ensemble 未就绪，12 次本地评分都截断，没有数值排名。
- [IdeaForecastBench 报告](../results/multi-bench-20261008T163557Z/idea-forecast-bench/report.md)。9 次生成完成，7 条严格格式合规。官方 embedding 不可用，本地 diagnostic 评分不完整，没有 Hit@5 或 MRR。
- [Comparative 报告](../results/multi-bench-20261008T163557Z/research-success-forecast/report.md)。三组 both-orders-correct 均为 1/4。Skills 一致性 4/4，但没有调用 leaf，不能解释为 leaf 的作用。

[ResearchClawBench 报告](../results/multi-bench-20261008T163557Z/researchclawbench/report.md)。Direct 和 Reflection 均在 1000 秒超时，产生代码、正确汇总表和 7/6 张 PNG，但报告代码的嵌套三引号错误导致 report.md 缺失。Skills 也遇到相同错误，随后自主修复并执行完整 pipeline，在 997.95 秒成功退出，交付 6 个代码文件、4626 词报告与 7 张图。路径为 reconstruct → assumption-map → contrast → minimal-experiment，4 次调用全部成功。主会话核对 15 张核心表，均与原始 CSV 一致，并核对报告、执行及归档哈希。

Skills 的 5 项有效最终 checklist 分数为 35、39、46、44、28，加权 38.38/100。两个 baseline 缺报告，分数保持 null。使用官方 prompt 与权重、本地 transport、同模型 judge，且公开资料缺目标论文与人工验证样本。图像 judge 仅接收报告前 10000 字符，不接收导出表。这些限制单独报告，没有补写候选报告、救援请求或重评。

本轮共 54 个候选任务，51 次原生成功、3 次超时、36 次成功 leaf 调用。ResearchClaw 的 9 次 setup probe 单列，不混入候选分母。其他三项完整评分缺失，所以无法形成全面数值排名。最清楚的反馈是输出格式、最终产物写入和评分器完整性需要优先解决，leaf 仍保持原来的简短内容。

[本轮总报告](../results/multi-bench-20261008T163557Z/report.md)与[机器可读汇总](../results/multi-bench-20261008T163557Z/summary.json)。
