# ResearchClawBench

[返回总览](../benchmarks.md)

## 测什么

要求 agent 执行完整研究任务，交付分析代码、结果、图表和研究报告。官方多模态 judge 按目标论文的 checklist 评估报告与图表，单项为 0 至 100 分，再取权重平均。50 表示与原论文相当。

官方项目为 [InternScience/ResearchClawBench](https://github.com/InternScience/ResearchClawBench)，[主页](https://internscience.github.io/ResearchClawBench-Home/)提供任务说明。judge 分数不能替代对代码、实验和结果的实际审查。

## 数据和运行位置

运行目录为 `/Users/junjie/Projects/idea-benchmarks/researchclawbench`。

- `tasks/` 为十个领域的官方 40 个任务，包含数据、相关论文和评测材料。
- `community/tasks/` 另存 HF 发布的 17 个社区任务。
- 默认 `--all` 只运行官方 40 个，不包含社区任务。
- `local/manifests/` 保存版本、文件哈希和任务数据路径检查。

公开静态输入已齐。框架环境已安装，各科学任务自己的训练、模拟、DFT 或其他领域软件需要在实际执行环境中配置。

## Agent 接口与交付物

agent 是一条 argv 命令，在官方创建的 workspace 中执行，接收 `{workspace}` 与 `{instructions}` 两个路径。

workspace 给 agent 的内容为 `data/`、`related_work/`、`INSTRUCTIONS.md`，不复制 `target_study/` 或评分 checklist。数据和参考目录只读。

按官方模板交付以下文件。

```text
workspace/
  code/                  分析代码
  outputs/               中间与最终结果
  report/report.md       方法、结果、讨论
  report/images/*.png    报告引用的图表
```

代码、非空报告和被报告引用的 PNG 是必需项。不要只写研究计划而没有执行证据。文件接口没有系统级沙箱，agent 的执行环境应限制读写范围。

## 配置并启动

复制配置样例到自己的新文件，填写实际 agent 路径和 judge 服务。

```bash
cd /Users/junjie/Projects/idea-benchmarks
cp researchclawbench/local/configs/agent.example.json /absolute/path/to/new-agent.json
cp researchclawbench/local/configs/judge.example.json /absolute/path/to/new-judge.json
```

agent JSON 使用 `argv`、`timeout_seconds`、`env` 和 `env_passthrough`，保留 `{workspace}`、`{instructions}` 占位符。真实配置的 `offline_fixture` 为 false。只把需要的 key 变量列入 `env_passthrough`。

judge JSON 使用 `mode: "live"`、`model`、`api_base`、`api_key_env`，模型必须能处理图像。样例读取 `JUDGE_API_KEY`，实际 key 在终端设置。

在独立的 experiment 配置中填写以下字段。

```bash
RESEARCHCLAW_AGENT_CONFIG=/absolute/path/to/new-agent.json
RESEARCHCLAW_JUDGE_CONFIG=/absolute/path/to/new-judge.json
RESEARCHCLAW_TASK=Astronomy_000
RESEARCHCLAW_ALLOW_OFFLINE_FIXTURE=0
```

```bash
./bench.sh researchclawbench ready
./bench.sh researchclawbench smoke
./experiment.sh researchclawbench /absolute/path/to/experiment.env
```

默认一个任务。设置 `RESEARCHCLAW_TASK=all` 才顺序执行官方 40 个任务。另检查社区数据可用 `./bench.sh researchclawbench ready --community`。

## 单独生成与评测

以下命令在公共运行目录执行。生成命令可重复 `--task ID`；输出目录必须不存在。

```bash
./bench.sh researchclawbench run \
  --agent-config /absolute/path/to/agent.json --task Astronomy_000 \
  --output-dir /absolute/path/to/new-generation --allow-network

./bench.sh researchclawbench evaluate \
  --run-dir /absolute/path/to/new-generation \
  --judge-config /absolute/path/to/judge.json \
  --output-dir /absolute/path/to/new-evaluation --allow-network
```

## 看结果与范围限制

一键结果保存在 `runs/researchclawbench/<run>/`。

- `generation/run-manifest.json` 记录任务、run ID、完成状态与输入输出哈希。
- 每个 generation workspace 保留代码、结果、图表和报告。
- evaluation 保存独立评分工作区与各任务的 `_score.json`，批次结果在 `evaluation/summary.json`。

只评完整且未改写的 generation 批次。缺报告、失败任务或不完整 checklist 结果不能计入成功覆盖。

自定义 argv 接口不要求使用 ResearchHarness。选择原始 ResearchHarness 路径时，另外需要其模型配置和 `SERPER_KEY`、`JINA_KEY`、`MINERU_TOKEN`。GPU 或容器需求由任务决定，静态数据检查通过不表示所有科学实验已在本机跑过。

更多配置与环境重建说明见运行目录的 `LOCAL.zh.md`。
