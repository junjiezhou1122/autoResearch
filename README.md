# AutoResearch

一个 Claude Code plugin，包含 `research-mode` 入口和 15 个研究 leaf skills。入口推荐适合当前研究情况的下一个 skill 或短 flow。每个 leaf skill 完成一个认知变换。

## 本地使用

在终端加载此插件：

```bash
claude --plugin-dir /Users/junjie/orca/projects/autoResearch
```

进入 Claude Code 后，输入入口命令并描述研究目前的位置：

```text
/autoresearch:research-mode 我已经理解这个方法的机制，想找出它依赖的关键假设。
```

入口推荐下一步后，调用对应 skill。也可以直接调用 `/autoresearch:reconstruct`、`/autoresearch:contrast` 等命令。`autoresearch` 是插件命名空间，`research-mode` 是入口名称。

## 插件结构

```text
autoResearch/
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

`.claude-plugin/plugin.json` 定义插件名称和版本。`skills/` 位于插件根目录，供 Claude Code 自动发现。后续 hooks 放在根目录的 `hooks/hooks.json`，相关脚本放在 `scripts/`。

[CLAUDE.md](CLAUDE.md) 只保存受控实验的 protocol。实验沿用已有的 `claude-research` 干净环境，通过 `--append-system-prompt-file` 显式加载同一份 protocol，再按 condition 选择是否通过 `--plugin-dir` 加载插件。命令与配置分工见 [配置说明](docs/configuration.md)。

## Skills

入口：[research-mode](skills/research-mode/SKILL.md)

| 分组 | Skills |
| --- | --- |
| Understand | [observe](skills/observe/SKILL.md)、[reconstruct](skills/reconstruct/SKILL.md)、[contrast](skills/contrast/SKILL.md)、[assumption-map](skills/assumption-map/SKILL.md)、[factorize-failure](skills/factorize-failure/SKILL.md)、[missing-mechanism](skills/missing-mechanism/SKILL.md) |
| Perturb | [assumption-break](skills/assumption-break/SKILL.md)、[unfreeze](skills/unfreeze/SKILL.md)、[boundary-push](skills/boundary-push/SKILL.md)、[counterfactual](skills/counterfactual/SKILL.md) |
| Invent | [transfer](skills/transfer/SKILL.md)、[close-loop](skills/close-loop/SKILL.md) |
| Filter & test | [prior-art-falsify](skills/prior-art-falsify/SKILL.md)、[prediction](skills/prediction/SKILL.md)、[minimal-experiment](skills/minimal-experiment/SKILL.md) |

## 验证

在插件根目录运行：

```bash
claude plugin validate .
```

根目录校验会提示 `CLAUDE.md` 不作为插件上下文自动加载。这个文件用于实验工作目录，加载方式见配置说明。skills 的名称、frontmatter 和路由链接已另行逐个检查。
