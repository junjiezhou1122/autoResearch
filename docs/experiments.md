# 实验记录

本文件保存各轮实验方法、结果和限制。方案、源码与进度进入 Git；`results/` 原始产物仅保留在本地，以下结果链接不随 clone 分发。当前插件 0.1.1 的路由执行规则尚未做模型复测，历史分数都属于各轮冻结入口。

首轮按 `experiments/pilot-plan.md` 做小规模真实调用，沿用已有 benchmark 数据和 `claude-research` 干净环境。

## Prompt 对照

不需要工具的任务通过 Magpie 的 OpenAI-compatible 接口调用 TokenDance。生成模型使用 `migrated-tokendance/mimo-v2.6-flash`。

三个 condition 使用相同任务、证据、温度和总输出上限，每项安排一次生成。所有组对 transport 错误都允许最多一次重试，模型截断与格式错误不重试。实际额外请求和未知的 timeout 用量另行报告：

| Condition | 输入差别 |
| --- | --- |
| direct | 任务与共同 protocol |
| reflection | 加上通用 draft、critique、revision 指令 |
| skill-prompt | 加上从当前 16 个 SKILL.md 读取的完整 suite |

完整 suite 作为 prompt reference，模型在单次回复中使用其中适合的操作。这与 Claude Code 的按需加载不同，也不等于原始设计中的 Random Primitives、Router Primitives 多步实验。

## 数据与评分

ResearchBench tiny 使用 12 个发布的研究问题和 inspiration 摘要，目标 hypothesis 不传给生成模型。生成提示使用本地单次调用模板，额外要求 80 至 150 英文词，而非官方多步生成流程，因此称为 ResearchBench tiny 数据上的本地 pilot，不能与已发表的官方结果直接比较。word-count 合规情况单独报告。

Research-success forecasting 使用 `test`、`sigma=1` 的前 12 个发布比较，共 24 个展示顺序。选择按已固定版本的 adapter 顺序，未按结果筛选。

方案预测使用现有本地论文定义评分器，主要指标要求同一比较的两个顺序都正确。作者 evaluator 不可获取，因此明确标记为 `LOCAL_PAPER_DEFINED_METRIC`。如果某组有失败或截断，pilot 按完整 12 个比较与 24 个展示的分母将该输出记错，并标记为 `FAILURE_AS_WRONG_PILOT_EXTENSION`，不冒充官方 scorer 成功。

ResearchBench 假设采用已安装项目的官方 `generation_score_prompt` 与 `parse_matched_score`，由另一模型家族 Ling-3.1-Flash 评分。judge 输入没有 condition 标签。匹配分衡量与目标假设的重合，不证明 novelty 或实际科研成功。

## 干净 runtime 验证

单独用 `claude-research` 加载插件并完成一个真实任务。仅开放 `Skill` 工具，防止模型读取本地目标答案。原始 stream 保存插件清单、MCP 清单、实际 Skill 调用与最终输出。这个 runtime 验证不混入 prompt 对照分数。

## 运行脚本

- `scripts/prompt_conditions.py` 从当前 skill 文件构建 condition prompt。
- `scripts/run_prompt_pilot.py` 调用模型，保存每次请求、响应、用量、失败和执行顺序。
- `scripts/comparative_pilot.py` 准备 label-free 输入，并调用现有 adapter 的评分函数。
- `scripts/score_research_pilot.py` 用官方评分 prompt 和 parser 做盲评，保存原始 judge 响应。
- `scripts/repair_judgments.py` 对每条失败的 judge 回复统一重试一次，保持评分 prompt、模型和温度不变，保留初次与重试记录。
- `scripts/run_clean_runtime.py` 在临时工作目录启动干净 Claude Code 并记录工具事件。
- `scripts/summarize_pilot.py` 汇总评分、配对差异、token 用量与实验限制。
- `scripts/check_pilot_runner.py` 只做本地客户端检查，其 fixture 输出不计入科研结果。

生成凭据通过环境变量或本地 Magpie gateway 注入，不保存上游 provider key。该环境的 Magpie 地址为 `http://127.0.0.1:3425/v1`。

## 结果范围

结果保存到独立的 `results/pilot-<UTC timestamp>/`。保留被中止的预算校准运行，避免把截断或空输出当作有效答案。报告需列出完整分母、失败、截断、实际返回模型、token 用量，以及任何评分或预算调整。

本轮是单一生成模型、小样本的 pilot。它可以发现明显的问题，不足以证明 skill suite 在全部科研任务上优于 baseline。费用只有在 provider 价格可验证时才估算。

## 本轮结果

首轮记录在 [完整报告](../results/pilot-20261008T040757Z/report.md)。生成使用 TokenDance MiMo-V2.6-Flash，judge 使用 Ling-3.1-Flash。

| Condition | ResearchBench tiny 匹配均分 / 5 | 方案比较两个顺序都正确 |
| --- | ---: | ---: |
| direct | 3.167 | 3/12 |
| reflection | 3.750 | 5/12 |
| skill-prompt | 3.167 | 3/12 |

本轮没有看到完整 suite prompt 的优势。样本量小，配对差异不足以支持稳定优劣判断。实际发生了 5 次 transport 重试，其中 skill-prompt 4 次、reflection 1 次；timeout 的上游 token 用量未知。所有评分、格式失败、token 用量与独立检查见报告及同目录原始记录。

干净 `claude-research` 已完成一个真实任务，stream 确认实际调用 `autoresearch:reconstruct`，没有 MCP servers。该结果仅证明 plugin 可执行，不计入上表。

## 第二轮，全部使用 Claude Code

用户选择实际使用方式，允许技能组多做步骤，并要求单次 prompt 调用 `/autoresearch:research-mode`，由 agent 自行路由、调用 skills 和停止。三组都使用干净 `claude-research`、同一 MiMo-V2.6-Flash[1m] 和原来的 12 个 ResearchBench tiny 问题。仅开放 Skill，无联网、文件、shell 或子 agent 工具；研究插件只在技能组加载。未修改入口和 leaf 内容，没有脚本追加用户回合或固定 leaf 次数。

[第二轮报告](../results/runtime-20261008T074000Z/report.md)保留所有原始回复、调用事件、用量和盲评。36 次原生进程均成功结束，但任务交付另行逐题检查。

| 方式 | 原始回复匹配均分 / 5 | 最终假设交付 | 单题中位耗时 | 输入 token，含缓存 | 输出 token |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 未完整评分，范围 3.17–3.58 | 12/12 | 15.5 秒 | 49,736 | 8,812 |
| Reflection | 3.25 | 12/12 | 18.5 秒 | 54,465 | 11,028 |
| 原生 research skills | 3.50 | 11/12 | 82.1 秒 | 331,177 | 31,395 |

技能组成功调用 30 次 skills。note05 在机制重构笔记处停止，官方匹配评分仍给这条原始回复 2 分。另行将未交付记零的本地分析给技能组 3.33 分，与 Reflection 差 0.08 分。该扩展不是官方 matched score。

首次 judge 有 5 条失败，统一各重试一次后得到 35/36 条有效评分。Direct 的 note01 两次都被截断，因此完整均分保持不可用；上表范围将缺失分数取 0 至 5 推导而来，没有从思考文本补分。技能组与 Reflection 的逐题匹配是 3 胜、9 平、0 负，小样本探索性检验不支持稳定提升。整体结论仍不确定，尚无证据说明额外消耗值得。

两条技能任务尝试了不可用的 Bash，运行时均拒绝，没有执行文件访问；Reflection 一题尝试了不存在的 hypothesis skill 后继续完成。实际 command markup 确认 12 个原生入口命令被识别，但 stream 不直接回放入口正文。`scripts/run_runtime_pilot.py` 记录单次原生任务，`scripts/summarize_runtime_pilot.py` 联合匹配分、交付审计、时间和用量汇总。

## 新入口规则，全量重跑

在 research-mode 增加一句整体任务完成与证据遗漏检查规则后，先单独复测 note05，再按用户要求重跑完整 12 题、三组共 36 次原生任务。Direct 与 Reflection 也重新生成。所有初始 prompt、模型、协议、15 个 leaf、600 秒超时和调度种子沿用第二轮，技能组只改变入口的这一句话。结果见[全量重跑报告](../results/runtime-revised-20261008T122704Z/report.md)。

| 方式 | 原始回复匹配均分 / 5 | 假设交付 | 字数合规 | 单题中位耗时 | 输入 token，含缓存 | 输出 token |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct | 3.167 | 12/12 | 12/12 | 17.5 秒 | 49,732 | 8,527 |
| Reflection | 3.333 | 12/12 | 12/12 | 31.1 秒 | 50,042 | 14,088 |
| 新入口 research skills | 3.417 | 11/12 | 9/12 | 106.6 秒 | 356,769 | 46,682 |

36 条评分已全部取得并核对原始响应，首次 3 条 judge 失败各按统一规则重试一次。技能组 32 次 Skill 调用全部成功，无工具错误。note05 完成了，但 note04 停在机制笔记并询问是否继续；note11、note12 有最终假设但混入中间产物，超出输出要求。因此新旧入口假设交付率均为 11/12，这次字数合规下降。

note04 原始回复仍获 3 分。将未交付按零分作本地额外分析后，技能组均分为 3.167，与 Direct 相同，低于 Reflection 的 3.333。技能组对 Direct 的逐题原始分数是 2 胜、8 平、2 负；对 Reflection 是 2 胜、7 平、3 负。当前小样本结果没有支持稳定质量提升，也没有显示新增一句改善了全量完成率。新旧轮的耗时和评分变化仅作描述，不能从一次随机重复归因于入口规则。`scripts/verify_runtime_pilot.py` 检查完整分母、原始 judge 分数、插件隔离和冻结 skill。

## 其他五项 benchmark 小样本，2026-10-09

用户授权快速并行测试其他 benchmark。四项文本使用 MiMo 2.6 Flash，ResearchClawBench 使用 gpt-6.1-sol。每项三组使用相同生成模型与证据，一次用户请求，自主选择操作，无固定 leaf 次数或救援回合。当前入口与 15 个 leaf 在整个 batch 中冻结。五项独立报告与原始材料见[本轮总报告](../results/multi-bench-20261008T163557Z/report.md)。

| Benchmark | 本轮范围 | 可验证结论 |
| --- | --- | --- |
| AI Idea Bench | 3 题 × 三组 | 9 次生成完成，Skills 原始格式 0/3。仅 6/27 条最终评分有效，无完整均分。 |
| AgentIdeaBench Static | 3 子领域，每组各 1 idea | 9 条假设交付。官方检索与 ensemble 缺失，12 次本地评分全部截断，无数值排名。 |
| IdeaForecastBench | 3 主题，2024-07 cutoff | 9 次生成完成，7 条严格格式合规。官方 embedding 缺失，本地诊断不完整，无 Hit@5/MRR。 |
| Comparative | 4 对方案，两个顺序 × 三组 | 三组 both-orders-correct 均为 1/4。Skills 一致性 4/4，但没有调用 leaf。 |
| ResearchClawBench | Earth_001 × 三组 | Direct/Reflection 超时缺报告；Skills 自主修复代码，997.95 秒完成，5 项 checklist 加权 38.38/100。 |

本轮共 54 个候选任务、51 次原生成功、3 次超时和 36 次成功 leaf 调用。ResearchClaw 的 9 次 setup probe 单独记录。主会话独立检查了 51 个文本 stream、ResearchClaw 全部 15 张核心表、完整 Skills 报告、实际执行和 5 条有效最终评分。Skills 的较具体机制与对照属于人工内容反馈，不能替代缺失的数值评分。

本轮是官方数据上的自定义 agent 对比，不是作者原始生成流程的复现。AI 的“Skills 原始格式 0/3”指本轮自定义的纯 JSON 保存外壳要求；作者生成器允许 THOUGHT 与 fenced JSON，并由程序提取，不能把本轮格式偏差直接称为不符合作者原始格式。AI 评分器曾使用 reasoning_content 作为最终评分，完整均分已撤回。AI 与 Forecast 的通用 treatment 前缀还保留 final hypothesis 字样，与各自 schema 冲突。ResearchClaw 使用官方 prompt 与权重但本地 transport 和同模型 judge；公开资料缺目标论文及人工验证样本，图像 judge 仅见报告前 10000 字符。所有限制均保留在报告中，没有重写候选输出或选择性重跑。当前结果没有支持稳定质量优势，最优先的反馈是最终格式、长报告落盘与评分完整性。

## AI Idea Bench 接入纠正后重跑，2026-10-09

用户要求先记录[接入约定](agent-benchmark-contract.md)，再重跑原来的 13、15、18 三题。通用 agent 说明与官方角色系统消息显式加载。三组使用实际 MiMo-V2.6-Flash，采用作者原始 idea_first_prompt 和七字段输出要求。adapter 在官方解析后添加 index 与 model_result。Skills 仅增加原生 /autoresearch:research-mode 入口，15 个 leaf 没有修改。没有候选墙钟截止、固定 leaf 顺序、调用上限或追加救援回合。

九次原生会话全部成功，官方解析与七字段交付均为 9/9。正式评分使用实际 Ling-3.1-Flash，27/27 次逻辑请求均在首次尝试返回有效最终 content，共产生 36 个标量评分。完整报告、逐题内容反馈与原始证据见[本轮报告](../results/ai-idea-official-task-20261009T072408Z/report.md)。

| 方式 | 动机相似度 / 5 | 实验相似度 / 5 | 动机主题对齐 / 5 | 实验主题对齐 / 5 |
| --- | ---: | ---: | ---: | ---: |
| Direct | 3.33 | 3.67 | 5.00 | 5.00 |
| Reflection | 3.00 | 3.33 | 5.00 | 5.00 |
| Skills | 3.33 | 3.33 | 5.00 | 5.00 |

Skills 的三次入口都被识别，但研究 leaf 调用为零。该样本没有展示 Skills 的质量提升，也没有检验到实际 leaf 方法执行。Skills 第 15 题缺 NEW IDEA JSON 标记，七字段 JSON 仍可正常提取。Direct 第 18 题成功加载两个 builtin skills，因此 baseline 有 builtin 技能影响。主题对齐全部为 5，区分力有限；目标相似度不能证明创新性、正确性或科研成功。

第一次全类型预检重现了动机评分的 JSON 模式问题。Magpie 与直连 TokenDance 均返回正常 stop、空最终 content 和非空 reasoning。去掉 response_format 后，两条路线均返回最终 fenced JSON。正式 transport 不传该参数，保留官方评分 prompt 与去代码块解析。三类预检全部通过后才启动候选，随后取得完整评分。该诊断证明所测请求可在上游边界复现，未区分底层模型与上游服务实现。

本轮使用本地 benchmark 接口的五篇缓存全文。作者的 SciPDF/GROBID 处理及 idea/experiment 摘要缓存不可用，因此不能宣称输入表示或已发表 baseline 的完全复现。作者模板 num_reflections 设为 1，Reflection 为本地通用反思对照。每题每组一次运行只提供探索性反馈。

单题中位耗时分别为 119.2、125.6、256.3 秒，并发为二。Skills 未缓存输入用量约为 Direct 的两倍，但没有 leaf 调用，底层原因尚未追踪，不能归因于额外研究操作。正式评分以外还有 11 次预检和诊断请求，本轮合计九次候选会话及 38 次 judge/诊断 HTTP 请求。原始 token、时间范围及费用未知项均在报告中。

[独立核验](../results/ai-idea-official-task-20261009T072408Z/verification.json)通过全部 stream、模型、工具、冻结哈希、参考输入和官方评分请求。最终审阅保留两个复现限制。完整评分目标源文件未冻结，但实际目标输入已随 request JSON 保存。冻结 runner 的旧汇总标签混入 builtin 调用，最终 summary 已通过后处理纠正，仓库 reporting 也已修正。冻结执行代码与科学输出未改动。旧实验及撤回的评分保持历史记录，不以新结果覆盖。
