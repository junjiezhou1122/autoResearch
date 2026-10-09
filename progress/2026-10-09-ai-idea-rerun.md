# AI Idea Bench 接入纠正与重跑

日期为 2026-10-09。本次沿用会话 6f2792f5-802a-49a7-a376-78c1abd74ffa。原始记录位于 /Users/junjie/.claude/projects/-Users-junjie-orca-projects-autoResearch/6f2792f5-802a-49a7-a376-78c1abd74ffa.jsonl。

用户明确要求先在 docs 记录接入原则，再重跑 AI Idea Bench。原则是官方提供什么 instruction 和 input 就使用什么，claude-research 负责研究执行，任务输出由官方 instruction 定义，adapter 只负责必要的输入转换、结果提取、保存和评分。

[接入约定](../docs/agent-benchmark-contract.md)已保存，[通用研究说明](../docs/research-agent.md)已创建。没有修改 15 个 leaf 或全局研究 profile。研究说明运行时显式加载，因为干净启动器关闭 CLAUDE.md 自动发现。

[本轮目录](../results/ai-idea-official-task-20261009T072408Z/plan.md)使用原来的 13、15、18 三题，MiMo 生成，Ling 评分，Direct、通用 Reflection 与原生 Skills 三组。使用作者原始生成模板和七字段输出，不再要求 hypothesis 或保存外壳。没有候选墙钟截止、leaf 次数限制或追加用户救援回合。

作者的 SciPDF/GROBID 预处理和 idea/experiment 摘要缓存本机不可用。新运行保留本地 benchmark 接口提供的五篇全文，并明确记录与作者摘要输入的差异，不宣称复现作者完整生成流程。原始模板 num_reflections 参数设置为 1，固定多轮策略由自主 agent 替代。Reflection 仍是本地对照，不是作者的两次显式反思。

三类评分预检先行。第一次动机相似度连续两次缺最终 content，挡住生成。随后用同一请求分别通过 Magpie 和直连 TokenDance，带 JSON 模式时均重现 content null，去掉模式时均得到最终 fenced JSON。最终 transport 不传 response_format，使用官方去代码块解析，只接受最终 content。三类预检全部通过后，才启动九次候选。

准备失败及第一次失败预检分别保存在 ai-idea-official-task-20261009T071407Z 和 ai-idea-official-task-20261009T071940Z。它们没有新候选输出。诊断证据见[动机评分诊断](../results/judge-channel-diagnostic-20261009T072113Z/report.md)。

当前状态为完成。九次原生会话均成功，官方解析器提取 9/9 份 idea，七字段完整交付 9/9。27/27 次正式评分均在首次请求返回有效最终 content，没有从 reasoning 补分。独立核验通过原始 stream、实际模型、工具结果、冻结文件与参考输入哈希、官方评分请求和完整均分。见[完整报告](../results/ai-idea-official-task-20261009T072408Z/report.md)和[核验记录](../results/ai-idea-official-task-20261009T072408Z/verification.json)。

| 方式 | 动机相似度 / 5 | 实验相似度 / 5 | 动机主题对齐 / 5 | 实验主题对齐 / 5 |
| --- | ---: | ---: | ---: | ---: |
| Direct | 3.33 | 3.67 | 5.00 | 5.00 |
| Reflection | 3.00 | 3.33 | 5.00 | 5.00 |
| Skills | 3.33 | 3.33 | 5.00 | 5.00 |

Skills 三次入口均被识别，但研究 leaf 调用为零，未展示 leaf 方法的质量提升。Skills 的第 15 题缺 NEW IDEA JSON 标记，七字段 JSON 仍能正常提取。Direct 第 18 题成功加载两个 builtin skills，并有一次失败查询，因此 baseline 不能称为完全无技能影响。

单题中位耗时 Direct 119.2 秒、Reflection 125.6 秒、Skills 256.3 秒。三组未缓存输入 token 分别为 286,313、271,566、540,592，缓存读取为 299,136、2,944、2,880，输出为 27,464、26,314、20,376。每题每组只有一次运行、并发为二，时间只作描述；Skills 输入用量偏高的底层原因未追踪。正式评分另计 31,893 prompt tokens 和 45,050 completion tokens。本轮共九次候选会话与 38 次 judge/诊断 HTTP 请求，包括 27 次正式评分和 11 次预检与诊断。

全文输入与作者摘要表示不同，不能宣称作者 baseline 复现。评分目标源文件未整体冻结，但实际评分输入均保存在 request JSON 中。冻结 runner 的旧汇总把 builtin 调用混入 leaf 计数；最终 summary 已通过单独后处理纠正，仓库 runner 的汇总标签也已改正，冻结执行代码保留不变。[审阅记录](../results/ai-idea-official-task-20261009T072408Z/review.md)保留这些复现限制。没有修改科学输出、leaf、全局 profile，也没有提交或推送。
