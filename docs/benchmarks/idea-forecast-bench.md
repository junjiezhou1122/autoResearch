# IdeaForecastBench

[返回总览](../benchmarks.md)

## 测什么

用截点以前的论文预测未来研究 idea，再检索截点之后的论文，判断问题与方法是否匹配。主要看 Hit@5 与 MRR，另有 Precision@5、soft score、cluster coverage 和 novelty 等诊断指标。它测未来方向预测，不测 idea 的实验成功。

官方项目为 [social-world-model/idea-forecast-bench](https://github.com/social-world-model/idea-forecast-bench)，数据为 [4R5T/idea-forecast-bench](https://huggingface.co/datasets/4R5T/idea-forecast-bench)。

## 数据、时间范围和运行位置

运行目录为 `/Users/junjie/Projects/idea-benchmarks/idea-forecast-bench`，官方源码在 `upstream/`。

- 完整发布包含 34 个 parquet，约 2.12 GB，108,768 条论文记录。
- `data/corpus/` 保存展开的 Markdown，约 8.27 GB。六条发布正文为空，原样保留；非空正文为 108,762 篇。
- 正式论文范围为 2024 年 4 月至 2025 年 9 月，loader 实际使用 63,855 篇非空论文。
- `data/catalog.json` 已核对 52 个主题、12 个截点、624 个任务。
- 截点从 2024 年 7 月至 2025 年 6 月，每个截点为该月第一天。

保留官方时间定义。历史为日期不晚于截点的论文，未来为截点之后到该月份加三个月的月底。`horizon_months=3` 会跨四个日历月，例如 2024-07 的未来范围结束于 2024-10-31。发布 Markdown 缺结构化发表日期时，官方 parser 从 arXiv ID 推断月末日期；本地保持该行为。

## Agent 接口

配置一条 command 数组，程序每次从 stdin 收一个任务，从 stdout 返回一个 JSON。日志写 stderr。

输入包含 `schema_version`、`task_id`、`topic`、`cutoff_month`、`cutoff_date`、`max_ideas` 和 `history`。历史论文含 ID、标题、日期、summary、keywords，不含未来论文或语料路径。

返回一至五个 idea，rank 必须从 1 连续递增。

```json
{
  "task_id": "llm_pretraining@2024-07",
  "ideas": [
    {
      "rank": 1,
      "problem": "具体问题与目标",
      "rationale": "历史论文支持这一预测的理由",
      "method": "提出的方法与机制",
      "key_terms": ["关键词"]
    }
  ]
}
```

不要读取或检索截点之后的信息来生成预测。输入字段隔离不是系统沙箱，也不能消除模型预训练中的未来论文知识。

## 配置并启动

复制两个样例到自己的新 JSON 文件。

```bash
cd /Users/junjie/Projects/idea-benchmarks
cp idea-forecast-bench/local/config/agent.example.json /absolute/path/to/new-agent.json
cp idea-forecast-bench/local/config/judge.example.json /absolute/path/to/new-judge.json
```

agent JSON 使用 `command`、`model_id`、`key_envs`、`timeout_seconds`、`fixture`。真实运行设 `fixture: false`，只在 `key_envs` 中列程序所需的凭据变量名。

judge JSON 需要两项服务。

- 模型 judge 使用 `judge_model`、`judge_base_url`、`judge_key_env`。
- embedding 使用 `embed_model: "voyage-3-large"`、`embed_base_url`、`embed_key_env`。

实际 key 在终端设置，两项服务分别可能收费。保持官方 embedding 模型，不随意换向量模型后仍声称同尺度评测。

在独立 experiment 配置中填写以下字段。

```bash
IDEA_FORECAST_AGENT_CONFIG=/absolute/path/to/new-agent.json
IDEA_FORECAST_JUDGE_CONFIG=/absolute/path/to/new-judge.json
IDEA_FORECAST_TASK=llm_pretraining@2024-07
IDEA_FORECAST_ALLOW_OFFLINE_FIXTURE=0
```

```bash
./bench.sh idea-forecast-bench ready
./bench.sh idea-forecast-bench smoke
./experiment.sh idea-forecast-bench /absolute/path/to/experiment.env
```

默认一个 topic/month，输入有 304 篇历史、436 篇未来论文。设置 `IDEA_FORECAST_TASK=all` 才跑全部 624 个任务。

## 单独生成与评测

以下命令在公共运行目录执行，可重复 `--task` 选择多个任务。输出目录必须是新的。

```bash
./bench.sh idea-forecast-bench run \
  --agent-config /absolute/path/to/agent.json \
  --task llm_pretraining@2024-07 --allow-network \
  --output-dir /absolute/path/to/new-generation

./bench.sh idea-forecast-bench evaluate \
  --run-dir /absolute/path/to/new-generation \
  --judge-config /absolute/path/to/judge.json --allow-network \
  --output-dir /absolute/path/to/new-evaluation
```

## 看结果与解释

一键结果保存在 `runs/idea-forecast-bench/<run>/`。生成结果在 `generation/predictions.json`，任务范围与 provenance 在 `generation/run.json`；评分在 `evaluation/evaluation.json`，另存 judge 状态与调用记录。

官方流程为每个 idea 检索十个候选，judge 分别给 problem、method、specificity 各 0 至 3 分。problem 加 method 至少 5，specificity 至少 2，才算 match。

Hit@5 表示前五个预测中是否至少有一个 match，MRR 衡量首个 match 的排名。上游 daily 榜单综合分为 `0.7 × Hit@5 + 0.3 × MRR`；当前 rolling backtest 输出各项汇总，不自动生成该榜单综合分。

Precision@5 是补充指标，固定除以 5，即使只生成一个 idea。读取 task_ids、scope 和 total_windows 后再解释汇总；单任务结果不是全部 624 个任务成绩。原始生成 CLI 若出现 matching skipped 的 NaN，表示未评分，不是有效模型分数。

报告模型版本、训练知识范围和检索约束，以便评估未来知识污染。更多 schema、数据恢复与时间定义见运行目录的 `LOCAL_README.md`，数据 receipt 在 `data/receipt.json`。
