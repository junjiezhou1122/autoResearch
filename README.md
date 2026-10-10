# AutoResearch

一个以 Claude Code plugin 实现的 research harness，用于组织研究 agent 的操作选择与执行。它包含 `research-mode` 入口和 15 个研究 leaf skills。入口根据当前研究状态选择有用的操作，加载对应 skill 执行，直到完成原任务要求的输出。每个 leaf skill 完成一个认知变换。

Claude Code 执行模型回合和工具调用；本项目定义研究路由与操作规则。Benchmark runner 负责接入任务、保存轨迹和评分，其脚本与实验材料保存在本地 `experiments/`，不随 GitHub 仓库分发。

## 本地使用

在终端加载此插件：

```bash
claude --plugin-dir /Users/junjie/orca/projects/autoResearch
```

进入 Claude Code 后，输入入口命令并描述研究目前的位置：

```text
/autoresearch:research-mode 我已经理解这个方法的机制，想找出它依赖的关键假设。
```

显式进入研究模式后，agent 必须先加载适用的 leaf，再执行对应研究工作，将中间结果用于继续完成原任务。你也可以直接调用 `/autoresearch:reconstruct`、`/autoresearch:contrast` 等命令。`autoresearch` 是插件命名空间，`research-mode` 是入口名称。

## 插件结构

```text
autoResearch/
├── .claude/
│   └── skills/
│       ├── create-adapter/
│       ├── harbor-adapter-creator/
│       └── sources.json
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── research-mode/
│   │   └── SKILL.md
│   └── ...
│       └── SKILL.md
├── CLAUDE.md
├── docs/
│   └── ...
└── README.md
```

`.claude-plugin/plugin.json` 定义插件名称和版本。`skills/` 位于插件根目录，供 Claude Code 自动发现。`.claude/skills/` 保存两份 benchmark 接入技能及其来源记录，使用方法见 [Harbor 接入流程](docs/benchmark-onboarding.md)。后续 hooks 放在根目录的 `hooks/hooks.json`，相关运行时脚本放在 `scripts/`。现有实验脚本位于 `experiments/scripts/`。

[CLAUDE.md](CLAUDE.md) 保存受控实验的 protocol。[通用研究说明](docs/research-agent.md)定义 agent 的自主执行和交付规则，具体输入与输出由任务决定。`claude-research` 关闭上下文文件的自动发现，运行时通过 `--append-system-prompt-file` 显式加载所需说明，再按 condition 决定是否加载插件。分工见[接入约定](docs/agent-benchmark-contract.md)和[配置说明](docs/configuration.md)。

## Skills

入口：[research-mode](skills/research-mode/SKILL.md)

| 分组 | Skills |
| --- | --- |
| Understand | [observe](skills/observe/SKILL.md)、[reconstruct](skills/reconstruct/SKILL.md)、[contrast](skills/contrast/SKILL.md)、[assumption-map](skills/assumption-map/SKILL.md)、[factorize-failure](skills/factorize-failure/SKILL.md)、[missing-mechanism](skills/missing-mechanism/SKILL.md) |
| Perturb | [assumption-break](skills/assumption-break/SKILL.md)、[unfreeze](skills/unfreeze/SKILL.md)、[boundary-push](skills/boundary-push/SKILL.md)、[counterfactual](skills/counterfactual/SKILL.md) |
| Invent | [transfer](skills/transfer/SKILL.md)、[close-loop](skills/close-loop/SKILL.md) |
| Filter & test | [prior-art-falsify](skills/prior-art-falsify/SKILL.md)、[prediction](skills/prediction/SKILL.md)、[minimal-experiment](skills/minimal-experiment/SKILL.md) |

## Agent 会话追溯

Entire 为仓库开发记录 agent 会话，并在提交时关联上下文。接入、验证和受控实验的隔离边界见 [Entire 配置说明](docs/entire.md)。

## Benchmark 接入与本地实验

现有 benchmark 入口见 [benchmark 总览](docs/benchmarks.md)。新增 benchmark 按 [Harbor 接入流程](docs/benchmark-onboarding.md)完成数据下载、adapter 验证和运行入口。

GitHub 仓库保存研究 plugin、使用文档与 benchmark 接入说明。本地 `experiments/` 集中保存实验方案、runner、进度、原始结果和工作日志，整个目录被 Git 忽略。普通 clone 不包含这些材料。本机客户端配置、会话捕获和缓存也不进入提交。

## 验证

在插件根目录运行：

```bash
claude plugin validate .
```

根目录校验会提示 `CLAUDE.md` 不作为插件上下文自动加载。这个文件用于实验工作目录，加载方式见配置说明。skills 的名称、frontmatter 和路由链接已另行逐个检查。
