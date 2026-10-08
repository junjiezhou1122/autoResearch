# 比较研究成功预测

[返回总览](../benchmarks.md)

## 测什么

给 agent 一个研究目标和两个方案的详细 idea 摘要，预测哪个方案的实证表现更好。它比较已有方案，不要求生成新 idea，也不执行新的科学实验。

论文为 [Teaching Language Models to Forecast Research Success Through Comparative Idea Evaluation](https://arxiv.org/abs/2605.21491)，作者公开数据为 [anikethh/Comparative-Idea-Evaluation](https://huggingface.co/datasets/anikethh/Comparative-Idea-Evaluation)。

原作者匿名仓库已过期，evaluator 和训练源码不可获取。本地使用公开数据与论文定义的评分实现，输出明确标记 `LOCAL_PAPER_DEFINED_METRIC`，不声称使用原作者代码。

## 数据和运行位置

运行目录为 `/Users/junjie/Projects/idea-benchmarks/research-success-forecast`。

公开文件保存在 `local/release/`，来源与哈希在 `local/evidence/release-manifest.json`。12 个文件共约 134 MB，七个 JSONL 共 24,386 条展示记录。

| Split | 独立比较 | 展示记录 |
| --- | ---: | ---: |
| train | 10,619 | 21,238 |
| test | 869 | 1,738 |
| cross_domain | 705 | 1,410 |

每个比较有原顺序与交换顺序两条展示，不能把展示行数当作独立比较数。论文的 11,488 对为 train 与主 test 之和，额外跨领域比较另报。

## Agent 接口与标签

agent argv 每次从 stdin 收一个 JSON task，从 stdout 返回一个 JSON。输入仅含 `task_id`、`comparison_id`、`split`、`sigma`、`idea_1`、`idea_2` 和 `research_goal`。idea 是从论文提取、去掉结果的详细方法摘要，不只是短 abstract。

输出恰好包含以下两个字段，label 为 JSON 整数。

```json
{"task_id":"输入中的ID","label":1}
```

**遵循发布数据的标签 convention。** `1` 表示 idea_1 获胜，`0` 表示 idea_2 获胜。这与论文正文的正式编号相反，不要自行翻转。

同一比较的两个顺序必须都预测。输入不包含真实标签、实证分数或 metric 字段；不可从磁盘读取答案来完成预测。

## 配置并启动

复制 agent 配置样例到自己的新 JSON 文件。

```bash
cd /Users/junjie/Projects/idea-benchmarks
cp research-success-forecast/local/agent-config.example.json /absolute/path/to/new-agent.json
```

JSON 使用 `argv`、`timeout_seconds`、`max_output_bytes`、非敏感 `env` 与凭据变量名 `env_passthrough`。实际 key 在终端设置。评分器使用公开标签，不需要模型 judge 或 embedding 服务。

在独立 experiment 配置中填写以下字段。

```bash
RESEARCH_SUCCESS_AGENT_CONFIG=/absolute/path/to/new-agent.json
RESEARCH_SUCCESS_SPLIT=test
RESEARCH_SUCCESS_LIMIT_PAIRS=1
RESEARCH_SUCCESS_ALLOW_OFFLINE_FIXTURE=0
```

```bash
./bench.sh research-success-forecast ready
./bench.sh research-success-forecast smoke
./experiment.sh research-success-forecast /absolute/path/to/experiment.env
```

默认一个主测试比较，即两次 agent 调用。设 `RESEARCH_SUCCESS_LIMIT_PAIRS=` 才使用完整 split。完整 test 为 1,738 次 agent 调用。train、test、cross_domain 分开报告，`all` 会混合所有发布 split。

## 单独生成与评测

以下命令在公共运行目录执行，输出目录必须不存在。

```bash
./bench.sh research-success-forecast run \
  --agent-config /absolute/path/to/agent.json \
  --split test --limit-pairs 1 --allow-network \
  --output-dir /absolute/path/to/new-generation

./bench.sh research-success-forecast evaluate \
  --run-dir /absolute/path/to/new-generation \
  --output-dir /absolute/path/to/new-evaluation
```

评分本身不调用网络。省略 `--limit-pairs` 使用完整选中 split；`--sigma 1|2|3` 可选主数据的难度组，参数以当前 `run --help` 为准。

## 看结果与指标

一键运行保存在 `runs/research-success-forecast/<run>/`。generation 保留 `tasks.jsonl`、`selection.json`、`predictions.jsonl`、`run.json`；结果在 `evaluation/evaluation.json`。

| 字段 | 含义 |
| --- | --- |
| consistency_aware_accuracy | 同一比较的两个顺序都选对才计正确，为主要比较指标 |
| consistency | 交换顺序后是否仍选中同一个方案 |
| presentation_accuracy | 单条展示预测正确率，为额外诊断指标 |
| by_sigma | 所选组别的单独统计 |

分数范围为 0 至 1。总选第一个方案的 fixture 在每对中只对一条，所以单条准确率为 0.5，但比较准确率和一致性都是 0；该结果只验证实现，不能作为方法成绩。

选择、任务与预测哈希都要通过验证。任务缺失、ID 重复、标签格式错误或运行产物被修改时，评分失败。

## 使用限制

发布数据保留重复比较的权重，train 与主 test 之间有一个相同的 unordered comparison、十个共享 idea 文本。不要静默去重或重切分后仍当作原发布成绩。

公开数据没有完整来源论文 ID、原始实证分数、reasoning 训练集或原作者模型回应，不能仅凭这些文件审计真实标签的生成过程。模型可能记住论文结果，输入字段隔离也不是系统级文件沙箱。

更多配置与本地 metric 定义见运行目录的 `local/LOCAL.md`。
