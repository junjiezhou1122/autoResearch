# ResearchBench

[返回总览](../benchmarks.md)

## 测什么

给 agent 一个研究问题和允许使用的 inspiration 摘要，要求生成科学假设。官方 judge 将预测与目标论文的假设和关键点比较，给出 0 至 5 分。它测假设内容的匹配，不能证明假设已通过实验。

官方项目为 [ankitala/ResearchBench](https://github.com/ankitala/ResearchBench)，数据为 [ankilok/ResearchBench](https://huggingface.co/datasets/ankilok/ResearchBench)。

## 数据和运行位置

运行目录为 `/Users/junjie/Projects/idea-benchmarks/researchbench`。

- `data/tiny/` 为小规模输入，每种任务 12 条。
- `data/full/` 为完整发布输入，包含 1,369 个 paper、1,367 个 retrieval、1,367 个 generation、1,323 个 ranking record。
- 自定义 agent 的一键流程使用 generation，full 分母为 1,367。
- `local/agent-inputs/` 是接口准备的生成输入，已去除目标 hypothesis、目标 DOI 和实验答案。

完整数据已下载并校验。该 HF 数据需要获准账号才能重新下载，使用与再发布须遵守数据条款。

## Agent 接口

将 agent 暴露为可执行程序，接受两个文件参数。

```bash
/absolute/path/to/agent --data INPUT.jsonl --out OUTPUT.jsonl
```

输入每行包含 `sample_id`、`discipline`、`research_question` 和 `gold_inspirations`。这里的 inspirations 是允许给定的论文标题与摘要，不是目标假设。

输出每个选中 ID 恰好一行，假设不能为空。

```json
{"sample_id":"输入中的ID","final_hypothesis":"完整科学假设"}
```

不要返回 `matched_score` 或 `matched_score_reason`。评分只能由 evaluator 产生。默认不传 background survey；比较方法必须保持相同输入设置。

## 配置并启动

先按[总览](../benchmarks.md)复制独立的实验配置，填写以下字段。key 在调用终端设置。

```bash
RESEARCHBENCH_AGENT=/absolute/path/to/agent
RESEARCHBENCH_SPLIT=tiny
RESEARCHBENCH_JUDGE_MODEL=YOUR_JUDGE_MODEL
# 终端需设置 OPENAI_API_KEY；自定义服务可另设 OPENAI_BASE_URL。
```

从公共运行目录执行。

```bash
cd /Users/junjie/Projects/idea-benchmarks
./bench.sh researchbench ready
./bench.sh researchbench smoke
./experiment.sh researchbench /absolute/path/to/experiment.env
```

tiny 是 12 个生成任务。将 `RESEARCHBENCH_SPLIT=full` 改为完整 1,367 个生成任务。

## 单独生成与评测

以下命令在公共运行目录执行，输出路径必须是新的。

```bash
./bench.sh researchbench run --split tiny \
  --agent /absolute/path/to/agent --out /absolute/path/to/new-ideas.jsonl

./bench.sh researchbench evaluate --split tiny \
  --pred /absolute/path/to/new-ideas.jsonl \
  --judge-model YOUR_JUDGE_MODEL --allow-provider-calls \
  --out /absolute/path/to/new-evaluation.json
```

生成程序自行管理自己的模型配置。`--allow-provider-calls` 允许评分器调用所选服务；没有这个开关就不做真实 judge 调用。

## 看结果

一键运行保存在 `runs/researchbench/<run>/`。

- `ideas.jsonl` 保存生成假设。
- `evaluation.json` 保存评分结果。
- 官方 matched score 范围为 0 至 5，汇总包含平均分除以 5 的结果。

缺失、重复、未知 ID 或不完整 judge 结果会导致失败。不要把未评分的任务忽略后宣称全量成功，也不要将 smoke 的固定分数用于方法比较。

更多接口与重建说明在运行目录的 `LOCAL_SETUP_zh.md`，数据清单在 `local/data-manifest.json`。
