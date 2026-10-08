# AgentIdeaBench

[返回总览](../benchmarks.md)

## 测什么

要求 agent 在给定子领域中提出有文献依据的科研假设。Static 使用固定参考摘要，Active 允许按官方协议检索文献。评测用文献证据和三个 critics 判断 originality、feasibility、clarity、impact、specificity。

官方项目为 [HKUST-KnowComp/AgentIdeaBench](https://github.com/HKUST-KnowComp/AgentIdeaBench)。评分不是实际实验验证。

## 数据和运行位置

运行目录为 `/Users/junjie/Projects/idea-benchmarks/agent-idea-bench`。

- `release_data/` 保存 51 份官方表格。
- `local_data/` 保存已补齐的 Static 输入与参考缓存，共 100 个子领域、828 条参考摘要。
- `scored40` 是官方密集评分的 40 个子领域，默认每个生成三个 hypothesis，共 120 条。
- `all` 为 100 个子领域，每个三个 hypothesis，共 300 条，应单独报告。

公开任务没有 train、validation、test 划分。Active 的未来检索请求和新假设的评测检索无法预先下载。

## Agent 与 judge 接口

实现可导入的 Python callback，例如 `my_agent:generate`。

callback 接收 `request: dict`，读取 `request['messages']`，返回以下形状。这里是接口示例，不是可用于实验的生成实现。

```json
{"content":"根据允许的参考提出的假设，正文为80至150英文词"}
```

Static request 包含 protocol、domain、subdomain、idea_index、messages、temperature 和 seed。保持原始提示、引用与确定性打乱，不自行加入目标答案。

评测另实现 `my_agent:judge`。请求有 `kind` 和 `critic_model`。

- `query_extraction` 返回 `content` 字符串，其中包含 JSON `queries`。
- `critic` 返回 `content` 字符串，其中包含五个评分维度，各有 1 至 10 的 `score` 与 `reasoning`。

使用请求中的官方 schema 与 prompt，不改评分规则。正式发表尺度要求按 `critic_model` 路由到 `qwen/qwen3.6-plus`、`moonshotai/kimi-k2.6`、`z-ai/glm-5.1`。用一个模型回答三次会改变评分尺度。

## 配置并启动 Static

按[总览](../benchmarks.md)准备独立实验配置。模块必须能在该仓库的 Python 环境中导入。

```bash
AGENT_IDEA_AGENT=my_agent:generate
AGENT_IDEA_JUDGE=my_agent:judge
AGENT_IDEA_COHORT=scored40
AGENT_IDEA_IDEAS=3
PYTHONPATH=/absolute/path/to/agent-package
# 终端需设置 SEMANTIC_SCHOLAR_API_KEY，以及 callback 使用的模型配置。
```

```bash
cd /Users/junjie/Projects/idea-benchmarks
./bench.sh agent-idea-bench ready
./bench.sh agent-idea-bench smoke
./experiment.sh agent-idea-bench /absolute/path/to/experiment.env
```

一键入口默认跑 Static、scored40、每个子领域三个 idea，并调用真实文献检索与 judge。首次小范围接入可用下面的单独命令。

```bash
./bench.sh agent-idea-bench run --protocol static \
  --agent my_agent:generate --cohort scored40 --limit 1 --ideas 1 \
  --allow-network --output /absolute/path/to/new-ideas.jsonl

./bench.sh agent-idea-bench evaluate \
  --input /absolute/path/to/new-ideas.jsonl --judge my_agent:judge \
  --cohort scored40 --ideas 1 --allow-network \
  --output /absolute/path/to/new-evaluation.jsonl
```

此小范围结果是 partial，不能与 scored40 全量指标等同。评测时 cohort 和每个子领域的 idea 数必须与生成一致。

## Active 模式

根目录一键入口只跑 Static。要运行 Active，用单独生成命令选择 `--protocol active`，并设置 Semantic Scholar key 与 `--allow-network`。

callback 每轮返回一个命令，最多十次工具调用。

```text
SEARCH: keyword query
FETCH: previously returned paperId
FINAL: one hypothesis paragraph of 80-150 words
```

FETCH 获取该论文的前 15 条参考，不是 PDF 下载。保持官方搜索循环与预算，检索失败不能算成功 rollout。

## 看结果与限制

一键运行保存在 `runs/agent-idea-bench/<run>/`。`ideas.jsonl` 和伴随 SQLite 数据库保存生成记录；`evaluation.jsonl` 及伴随 summary 保存文献、critic 回应、分数和覆盖范围。

官方聚合在每个维度去掉三个 critic 的最大值，再按 `O=2、I=1.5、F=1、C=0.5、S=0.5` 加权，除以 5.5。prior art 截止为 `2026-05-31`，不得随意改成今天。

已有 JSONL、数据库或 sidecar 文件不会覆盖。公开历史评测证据中的全部摘要未补齐，私有数据的 redaction 审计也不能复现；Static 的 828 条生成参考已齐，不等于新假设可完全离线评测。

更多 schema 与 Active 参数见运行目录的 `LOCAL_SETUP.md`。
