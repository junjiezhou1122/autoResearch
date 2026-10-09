# 研究技能构建与实验会话

记录更新日期：2026-10-09。主要实验运行日期为 2026-10-08，会话延续到 2026-10-09。

## 会话定位

- Session ID：`6f2792f5-802a-49a7-a376-78c1abd74ffa`。
- 项目：`/Users/junjie/orca/projects/autoResearch`。
- 本机原始对话：`/Users/junjie/.claude/projects/-Users-junjie-orca-projects-autoResearch/6f2792f5-802a-49a7-a376-78c1abd74ffa.jsonl`。
- 接续命令，在该项目目录运行：`claude --resume 6f2792f5-802a-49a7-a376-78c1abd74ffa`。此命令未在本次记录工作中执行。

原始对话文件在记录时确认存在。路径是本机定位信息，其他机器不一定有此文件。本文是进展整理，原始对话和实验文件提供具体依据。

## 思路与工作如何推进

### 确定最小插件形态

建立 15 个简短研究 leaf 和 `research-mode` 入口，打包为 `autoresearch` plugin。用户明确要求保持 leaf 简短，只做必要格式完善，不扩写研究方法。入口采用手写导航，不能退化成泛化研究原则或只有状态分类。

使用已有干净 `claude-research` 环境，添加实验 protocol 和配置说明。历史对话中提到的 PDF 不属于本次任务，没有制作。hooks 留待后续。

### 首轮先比较提示

在同一模型上比较 Direct、Reflection 和完整 suite prompt。ResearchBench tiny 匹配均分为 3.167、3.750、3.167。另做了干净 Claude Code 下真实 leaf 调用验证。

这轮完整 suite 是单次 API 提示，不是动态加载或原生路由。因此结果只能说明这个提示方案未显示优势。

证据：[首轮报告](../results/pilot-20261008T040757Z/report.md)。

### 改为真实的自主 agent 比较

用户选择实际使用效果，允许 Skills 多做步骤，同时记录时间和 token。通过讨论确定以研究假设生成为任务，采用 ResearchBench tiny。

用户纠正了两用户回合编排及固定调用次数的方案。最终使用一次以 `/autoresearch:research-mode` 开头的请求，agent 自己调用 skills、继续和停止。

三组均使用干净 Claude Code、同一模型和证据；仅开放 Skill，禁用候选文件、shell、web 和子 agent 工具。目标答案只用于评分。技能组通过原生插件加载，基线不加载该研究插件。

证据：[原生实验方案](../experiments/claude-code-plan.md)。

### 全原生实验发现交付失败

完成 12 题 × 3 组，共 36 次原生候选生成。Skills 成功调用 30 次，交付 11/12 个假设。note05 在 reconstruct 机制笔记处结束。运行成功和研究任务交付因此独立记录。

盲评最终取得 35/36 条有效分数。Direct 均分不可用，完整均分范围 3.17–3.58；Reflection 为 3.25，Skills 为 3.50。将 Skills 未交付按零分作独立本地分析后为 3.333。小样本没有支持稳定优势。

证据：[原生实验报告](../results/runtime-20261008T074000Z/report.md)。

### 检查轨迹，尝试一句完成检查

轨迹分析发现，额外操作常在细化基线已能生成的核心答案，也未稳定覆盖参考材料中的相关信息。评分目标与新颖预测并不完全一致，judge 也存在限制。

对 note05，最有依据的解释是局部操作完成后没有可靠回到整体交付目标。用户要求在入口加一句完成与证据遗漏检查，并单独复测。note05 通过 reconstruct → assumption-map → prediction 交付了 109 词假设。

证据：[note05 复测报告](../results/entry-check-20261008T114106Z/report.md)。

### 用户澄清要全量重跑

用户进一步明确要求全部题目按新入口重跑。完成另一次 36 条生成和 36 条有效盲评。

| 方式 | 匹配均分 | 假设交付 | 字数合规 | 单题中位耗时 |
| --- | ---: | ---: | ---: | ---: |
| Direct | 3.167 | 12/12 | 12/12 | 17.5 秒 |
| Reflection | 3.333 | 12/12 | 12/12 | 31.1 秒 |
| Skills | 3.417 | 11/12 | 9/12 | 106.6 秒 |

note05 完成，但 note04 停在机制重构并说“Say the word and I'll carry it out”。note11、note12 有假设但附带中间笔记。Skills 的 32 次调用全部成功，因此工具成功不能解释为最终交付成功。

note04 的原始回复虽未交付假设，仍获匹配分 3。将未交付计零后 Skills 均分为 3.167，与 Direct 相同。该敏感性分析不是官方指标。

证据：[全量重跑报告](../results/runtime-revised-20261008T122704Z/report.md)、[第四题提前停止回复](../results/runtime-revised-20261008T122704Z/main/calls/note04/skill-prompt/output.txt)、[完整核验](../results/runtime-revised-20261008T122704Z/verification.json)。

### 明确自主完成标准，快速重跑第四题

用户明确反对中途请求确认，提出把原始任务的 input → output 与完成条件说清楚。经讨论，将入口完成句替换为以原始输出为标准，利用中间结果自主继续，无需操作间确认。所有 leaf 保持原样。

用户授权只快速重跑 note04 一次。新轨迹为 reconstruct → assumption-map → boundary-push → prediction，交付 114 词假设正文，耗时 258.2 秒，没有新增 judge 调用。回复有一个简短标题，没有中间笔记和等待确认。

中途用户中断的是等待结果的检查命令，后台实验之后正常结束。后续读取最终回复确认了交付，未因中断再启动候选生成。

证据：[最新单题报告](../results/autonomy-check-20261008T132400Z/report.md)、[最终回复](../results/autonomy-check-20261008T132400Z/main/calls/note04/skill-prompt/output.txt)、[输入一致性检查](../results/autonomy-check-20261008T132400Z/input-verification.json)。

### 评估内容，并建立接续记录

对最新回复的人工分析认为其机制具体且合理，但属于自然的方法组合，未证明明显新颖性。现有实验性能不能直接迁移到组合系统，培养液中的关联在全血里能否保留也需要验证。

用户调用 timeline 回顾思路，随后要求建立 `progress/` 保存当前状态、会话 ID 和进展。本目录是该明确请求的结果。

## 当前结论与接续边界

已验证最新规则下 note04 的一次自主交付。最新规则尚未全量验证，也没有新增质量评分。已有全量实验没有支持稳定的 Skills 质量提升。下一次接续时先读[当前状态](current.md)。

继续保持一个请求、自主选择和停止。leaf 保持简短。不要用脚本追加确认回合或固定操作序列修饰完成率。候选不能访问隐藏目标或评分材料。

本会话实验授权范围内的运行已完成。进一步模型调用需要依据后续用户任务确定范围。没有创建提交或推送，没有保存凭据或复制整个原始对话到项目。
