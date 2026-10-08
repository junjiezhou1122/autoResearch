# AI Idea Bench 2025

[返回总览](../benchmarks.md)

## 测什么

给 agent 一个研究主题和五篇参考论文文本，要求提出研究动机与实验计划。当前一键评测使用官方 IGI 和 IGT，分别比较生成 idea 与目标 idea、主题的关系。它测 idea 内容与计划质量，不执行生成的实验。

官方项目为 [AI_Idea_Bench_2025](https://github.com/yansheng-qiu/AI_Idea_Bench_2025)。

## 数据和运行位置

运行目录为 `/Users/junjie/Projects/idea-benchmarks/ai-idea-bench`。

- 共 3,495 个任务，每个任务给五篇参考论文。
- 去重后有 8,840 份本地参考文本，保存在 `data/paper_text/`。
- 任务与文本映射及校验记录在 `data/manifest.json`。
- 完整原始 PDF ZIP 保存在 `hangzhou_server:/home/zhoujunjie/idea-benchmarks-20261008/archives/Idea_bench_data.zip`。

本地日常运行使用已提取文本，不需要下载整包 PDF。

## Agent 接口

配置一条可执行命令。入口为每个任务启动一次进程，通过 stdin 传一条 JSON，stdout 返回一条 JSON。日志写 stderr。

输入包含 `index`、`topic` 和五项 `references`。每项参考有标题、全文 `text` 及来源路径，不含目标论文的 motivation 或 method 字段。

输出保留输入整数 `index`，`model_result` 为非空数组。

```json
{
  "index": 13,
  "model_result": [
    {
      "Motivation": "研究问题与动机",
      "Experiment": "方法与实验计划"
    }
  ]
}
```

两个 idea 字段都必须是非空字符串。可额外返回 `Title`，不可缺失或重复任务 ID。

## 配置并启动

先按[总览](../benchmarks.md)准备独立实验配置，填以下字段。

```bash
AI_IDEA_AGENT_COMMAND='/absolute/path/to/python /absolute/path/to/agent.py'
AI_IDEA_JUDGE_MODEL=YOUR_JUDGE_MODEL
AI_IDEA_LIMIT=1
# 终端需设置 BENCH_API_KEY 和 BENCH_BASE_URL。
```

`BENCH_BASE_URL` 是所选 OpenAI-compatible 服务地址。生成 agent 自行读取自己的模型配置。

```bash
cd /Users/junjie/Projects/idea-benchmarks
./bench.sh ai-idea-bench ready
./bench.sh ai-idea-bench smoke
./experiment.sh ai-idea-bench /absolute/path/to/experiment.env
```

默认先跑一个任务。设 `AI_IDEA_LIMIT=` 才执行全部 3,495 个；指定正整数则运行对应数量的子集。

## 单独生成与评测

以下命令在公共运行目录执行，选择新的输出目录。

```bash
./bench.sh ai-idea-bench run \
  --agent-command '/absolute/path/to/python /absolute/path/to/agent.py' \
  --limit 1 --output /absolute/path/to/new-generation

./bench.sh ai-idea-bench evaluate \
  --predictions /absolute/path/to/new-generation/final_ideas.json \
  --metrics igi,igt --model YOUR_JUDGE_MODEL --allow-network \
  --output /absolute/path/to/new-evaluation
```

## 看结果与范围限制

一键运行保存在 `runs/ai-idea-bench/<run>/`。主要读取 `generation/final_ideas.json` 与 evaluation 目录中的评分和状态文件。状态记录选中任务覆盖和全量 3,495 条分母，子集结果不能报告为全量成绩。

官方 IGI 外层的 `motivation_similarity` 与 `experiment_plan_similarity` 命名存在反置。本地保持原始行为，分析时按嵌套 judge response 的含义解释，不只看外层字段名。

使用时保留以下限制。

- 当前接入可跑 IGI、IGT，不代表上游全部指标可用。MCQ、novelty、competition 等还缺部分发布资产，fixture 不能替代正式资产。
- 全文来自 PyMuPDF 与部分 OCR，不等同于原始 SciPDF/GROBID 解析；图、布局与部分公式可能丢失。
- 两份官方 PDF 只有封面或索引，已保留真实来源，不能补造正文。
- 部分上游 topic 回退字段可能有答案线索，比较方法必须使用相同任务输入。

更多说明在运行目录的 `LOCAL_README.md`。
