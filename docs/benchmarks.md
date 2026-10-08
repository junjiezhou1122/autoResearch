# Benchmark 总览与运行入口

本项目使用六个 benchmark，分别测试科研 idea 生成、未来方向预测、方案比较和研究执行。先选择评测目标，再按对应文档接入 agent。

## 有哪些 benchmark

| Benchmark | 测什么 | Agent 产出 | 数据范围 | 操作说明 |
| --- | --- | --- | --- | --- |
| ResearchBench | 根据研究问题和参考摘要提出科学假设，与论文目标假设比较 | 假设文本 | tiny 12 个生成任务；full 1,367 个生成任务 | [ResearchBench](benchmarks/researchbench.md) |
| AI Idea Bench 2025 | 根据主题和参考论文提出动机与实验计划 | Motivation、Experiment | 3,495 个任务，8,840 份参考文本 | [AI Idea Bench](benchmarks/ai-idea-bench.md) |
| AgentIdeaBench | 在子领域中提出有文献依据的假设，支持固定参考和主动检索 | 80 至 150 英文词的假设 | 100 个子领域；默认评测 cohort 为 scored40 | [AgentIdeaBench](benchmarks/agent-idea-bench.md) |
| ResearchClawBench | 执行完整研究任务并交付可审查的结果 | 代码、结果、PNG、研究报告 | 官方 40 个任务；另存 17 个社区任务 | [ResearchClawBench](benchmarks/researchclawbench.md) |
| IdeaForecastBench | 用过去论文预测未来论文会探索的 idea | 最多五个排序后的 idea | 52 个主题，12 个截点，624 个任务 | [IdeaForecastBench](benchmarks/idea-forecast-bench.md) |
| Comparative Idea Evaluation | 预测给定的两个方案谁的实证表现更好 | 获胜方案标签 | 主测试 869 个比较；每个比较有两个展示顺序 | [比较研究成功预测](benchmarks/research-success-forecast.md) |

这些分数不能直接横向比较。未来论文匹配不等于实验成功；idea 相似度和 judge 分数也不能代替实际实验。

## 文档、程序和数据在哪

本目录只保存操作文档。当前已配置的程序、独立 Python 环境和数据在另一目录。

```text
/Users/junjie/orca/projects/autoResearch/docs/
  benchmarks.md                  总览
  benchmarks/*.md               各 benchmark 操作说明

/Users/junjie/Projects/idea-benchmarks/
  bench.sh                      检查、生成和评测入口
  experiment.sh                 一键生成后评测
  experiment.env.example        配置模板
  <benchmark>/.venv/            独立环境
  <benchmark>/                  程序、数据和本地接口
  runs/<benchmark>/<run>/        实验结果
  reports/                      数据与验收证据
```

将来迁移运行目录时，更新文档中的绝对路径。文档目录不是 benchmark 的执行目录。

## Agent 操作顺序

1. 读对应 benchmark 文档，确认输入、输出、任务范围和评分含义。
2. 在运行目录检查环境与数据。
3. 为当前实验创建独立配置文件，接入自己的 agent 和所需评分服务。
4. 先跑小范围任务，确认输出完整，再扩大范围。
5. 保存配置、模型版本、任务范围、输出和评分；把 fixture 与真实结果分开。

检查不需要真实模型调用。

```bash
cd /Users/junjie/Projects/idea-benchmarks
./bench.sh all doctor
./bench.sh all ready
./bench.sh researchbench smoke
```

`doctor` 检查环境，`ready` 检查发布输入，`smoke` 用 fixture 或回放检查流程。smoke 分数没有科学意义。需要检查某一项时，将 `researchbench` 换成表中的目录名。

## 一键运行

为每个实验复制一份配置模板，只填当前 benchmark 所需字段。已有配置不要覆盖。

```bash
cd /Users/junjie/Projects/idea-benchmarks
cp experiment.env.example /absolute/path/to/new-experiment.env
# 编辑 new-experiment.env，填写 agent 和评分配置。
./experiment.sh researchbench /absolute/path/to/new-experiment.env
```

可选名称为 `researchbench`、`ai-idea-bench`、`agent-idea-bench`、`researchclawbench`、`idea-forecast-bench`、`research-success-forecast`。省略第二个参数时，读取运行目录的 `experiment.env`。

配置文件按 shell 文件加载。命令、JSON 配置和模型 key 都要明确提供，key 不写进仓库或实验报告。需要真实 provider 的调用可能收费。

每次一键运行创建新的 `runs/<benchmark>/<时间与进程ID>/` 目录，成功后打印 `Results:` 路径。单独生成或评测的参数以当前 CLI 为准。

```bash
./bench.sh idea-forecast-bench run --help
./bench.sh idea-forecast-bench evaluate --help
```

## 实验约束

- 遵循分配的实验条件，只使用允许的知识、证据、工具和预算。
- 仅在实验条件允许时检索网络；CLI 的网络开关不改变实验条件。
- 不给生成 agent 传入目标答案、未来论文、真实胜负标签或评分材料。
- 不修改官方时间切分、提示词、任务范围或评分定义来提高分数。
- 子集与全量分别报告，保持比较方法的输入和预算一致。
- 文件接口不提供系统级沙箱。真实 agent 应在自身执行环境中限制文件访问。

## 当前准备状态

2026-10-08 的验收覆盖六个入口的 help、doctor、smoke、ready，共 24 个命令，均通过。六个一键入口也通过 fixture 验证。正式科学 agent、真实模型评分和任务专用训练或模拟尚未运行。

Comparative Idea Evaluation 使用作者公开数据和明确标记的本地论文定义评分器，原作者 evaluator 源码不可获取。其他限制见各 benchmark 文档。

重新检查实际状态可运行以下命令，证据保存在运行目录的 `reports/verification.json`。

```bash
cd /Users/junjie/Projects/idea-benchmarks
python3 verify.py
```
