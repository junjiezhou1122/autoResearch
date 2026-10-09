# 本地实验脚本

这些脚本保存 2026-10-08 至 2026-10-09 的实验执行与核验代码。它们依赖本机 benchmark checkout、模型代理和历史结果目录，不能在普通 clone 后直接复现完整实验。原始数据和结果被 Git 忽略，方法、有效评分分母与限制见[实验记录](../docs/experiments.md)和[进度](../progress/README.md)。

## 文件分工

| 文件 | 用途 |
| --- | --- |
| `prompt_conditions.py` | 构建首轮 Direct、Reflection 与完整 suite prompt 条件 |
| `run_prompt_pilot.py` | 单次 API 生成并保存请求、回复和用量 |
| `comparative_pilot.py` | 准备比较任务并调用本地 adapter |
| `score_research_pilot.py` | 使用 ResearchBench 官方 prompt 和 parser 盲评 |
| `repair_judgments.py` | 对历史失败评分统一重试一次 |
| `run_clean_runtime.py` | 早期单任务原生 Skill 调用验证 |
| `run_runtime_pilot.py` | 历史 ResearchBench 三组原生 Claude Code 运行 |
| `summarize_pilot.py` | 首轮固定数据与历史结果汇总 |
| `summarize_runtime_pilot.py` | 联合原生评分、交付审计、时间和用量 |
| `verify_runtime_pilot.py` | 核对历史 stream、评分与插件隔离 |
| `check_pilot_runner.py` | 本地 fixture 检查，不调用模型 |
| `run_ai_idea_agent.py` | AI Idea 任务接口的准备、预检、生成、评分和汇总 |
| `verify_ai_idea_agent.py` | 核对 AI Idea 原始 stream、冻结来源与评分请求 |

## 运行依赖

使用 Python 3。部分 API 脚本需要 `httpx`。ResearchBench 脚本需要其运行环境中的官方模块、数据和 prompts；Comparative 使用已有本地 adapter；AI Idea 使用 `/Users/junjie/Projects/idea-benchmarks/ai-idea-bench`。代码中的绝对路径保留了历史环境，运行前需逐项核对，不能把路径存在视为依赖已验证。

原生会话通过 `/Users/junjie/.local/bin/claude-research` 启动。该启动器的隔离设置不在本仓库，参见[配置说明](../docs/configuration.md)。当前模型代理地址为 `http://127.0.0.1:3425/v1`。judge 脚本中的 `Bearer magpie` 是本地代理的占位认证值，不是 TokenDance 上游凭据。真实 provider key 不保存在源码、请求文件或进度中。

读取下载的 benchmark 代码时使用隔离 Python 模式，并从本仓库运行脚本。部分历史脚本仍会导入外部 benchmark 模块或执行从其源码提取的函数，使用前需信任和核对这些来源。

## 历史边界

运行前阅读对应脚本参数、实验方案和本轮报告。生成、预检、judge 与重试入口会发起可能收费的 provider 调用，需单独明确授权。校验器和汇总器也会写文件，复跑可能覆盖派生产物。新运行使用新的本地 `results/` 子目录，保留旧请求与输出。

`run_runtime_pilot.py` 是历史受限工具实验，只开放 `Skill`，MCP 为空，并使用当时的候选超时。`run_clean_runtime.py` 是更早的探针，没有同等的显式 MCP 限制或进程组清理。它们不代表当前 agent 的完整科学代码执行能力。

`run_ai_idea_agent.py` 的预检读取一份历史未提交的评分请求。候选没有墙钟超时或显式花费上限。评分读取 live target 源文件，prepare 没有冻结整个 target 文件；实际评分输入保存在每条 request JSON。作者 IGI 外层保存键是交换的，脚本保留其布局，汇总按内层语义解释。当前汇总区分 builtin Skill 调用与 research leaf，历史冻结 runner 的纠正方式见本轮报告。

历史汇总需要人工交付审计或字数合规输入，部分统计和验证器固定任务数、目录结构与当时结论。源码保存便于检查当时流程，不能替代缺失的 benchmark 数据、原始产物和人工审计。
