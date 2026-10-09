# AutoResearch

一个 Claude Code plugin，包含 `research-mode` 入口和 15 个研究 leaf skills。入口根据当前研究状态选择有用的操作，加载对应 skill 执行，直到完成原任务要求的输出。每个 leaf skill 完成一个认知变换。

## 本地使用

在终端加载此插件：

```bash
claude --plugin-dir /Users/junjie/orca/projects/autoResearch
```

进入 Claude Code 后，输入入口命令并描述研究目前的位置：

```text
/autoresearch:research-mode 我已经理解这个方法的机制，想找出它依赖的关键假设。
```

入口自主选择并加载有用的 skill，将中间结果用于继续完成原任务。你也可以直接调用 `/autoresearch:reconstruct`、`/autoresearch:contrast` 等命令。`autoresearch` 是插件命名空间，`research-mode` 是入口名称。

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
│   └── configuration.md
└── README.md
```

`.claude-plugin/plugin.json` 定义插件名称和版本。`skills/` 位于插件根目录，供 Claude Code 自动发现。`.claude/skills/` 保存两份 benchmark 接入技能及其来源记录，使用方法见 [Harbor 接入流程](docs/benchmark-onboarding.md)。后续 hooks 放在根目录的 `hooks/hooks.json`，相关脚本放在 `scripts/`。

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

## 进度记录

[progress/](progress/README.md)保存当前状态与会话进展。接续工作先看[当前状态](progress/current.md)；历史会话记录包含 session ID、原始对话路径、关键决定和实验材料链接。

## 实验

现有 benchmark 入口见 [benchmark 总览](docs/benchmarks.md)，各轮方法、结果与限制见 [实验说明](docs/experiments.md)。后续新增 benchmark 按 [Harbor 接入流程](docs/benchmark-onboarding.md)完成数据下载、adapter 验证和一键运行入口。

Git 保存插件、文档、实验脚本、方案与 `progress/` 进度。`results/` 的原始请求、回复、评分和产物仅保留在本地，不进入提交；本机客户端配置、会话记录、缓存和工作日志也被忽略。文档中的 `results/` 链接需要本地实验目录，普通 clone 没有这些文件。脚本的环境要求与历史运行边界见 [scripts/README.md](scripts/README.md)。

## 验证

在插件根目录运行：

```bash
claude plugin validate .
```

根目录校验会提示 `CLAUDE.md` 不作为插件上下文自动加载。这个文件用于实验工作目录，加载方式见配置说明。skills 的名称、frontmatter 和路由链接已另行逐个检查。
