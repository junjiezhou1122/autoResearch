# 插件与实验配置

## 插件包装

插件名是 `autoresearch`，入口名是 `research-mode`。入口命令为 `/autoresearch:research-mode`，leaf 命令也使用 `autoresearch` 命名空间，避免与环境中已有的同名 skills 混淆。

`.claude-plugin/plugin.json` 保存插件元数据。全部 16 个 skills 位于根目录的 `skills/`，由 Claude Code 自动发现。

## 入口与 leaf skills

`research-mode` 是一张导航地图。它根据当前研究情况推荐下一个 skill 或短 flow，推荐后停止。`disable-model-invocation: true` 让这个入口由用户显式调用。

15 个 leaf skills 各自保留一个认知变换的极简正文。它们的 `name` 和 `description` 用于发现，正文按需加载。

## CLAUDE.md

仓库根目录的 `CLAUDE.md` 保存受控实验的 protocol，约束证据范围、联网权限、research state、预算和最终输出 schema。具体任务提供 evidence package、预算数值和 benchmark schema。

Claude Code 不会因为加载 plugin 就自动加载其中的 `CLAUDE.md`。普通启动时，工作目录的 `CLAUDE.md` 可以被自动发现；下面的研究启动器关闭了这项自动加载，因此实验显式注入同一份 protocol。

## 已有的干净研究环境

实验沿用本机的 `/Users/junjie/.local/bin/claude-research` 启动器。它使用独立的 `CLAUDE_CONFIG_DIR=/Users/junjie/.claude-research`，只读取该目录的 user settings，跳过 project 和 local settings，关闭 Chrome 集成、自动加载 `CLAUDE.md` 与 `AGENTS.md`，以及自动记忆。它还清除选定的继承环境变量，避免沿用日常插件目录与 skill catalog。

这个 profile 建立时只复制了模型连接设置，没有复制日常 hooks、plugins 或 skills。启动器使用正常运行模式，保留内置功能，也允许明确加载研究 skills、plugins 和后续 hooks，因此不用 `--safe-mode` 或 `--bare`。

Baseline 启动时显式带入 protocol：

```bash
claude-research \
  --append-system-prompt-file /Users/junjie/orca/projects/autoResearch/CLAUDE.md
```

Primitive condition 额外加载本插件：

```bash
claude-research \
  --append-system-prompt-file /Users/junjie/orca/projects/autoResearch/CLAUDE.md \
  --plugin-dir /Users/junjie/orca/projects/autoResearch
```

各 condition 在各自的实验工作目录启动。仅把 `CLAUDE.md` 复制到工作目录不会让这个启动器加载它。`--plugin-dir` 只对当前会话生效；对照实验使用这种加载方式，避免把 treatment 插件永久装进共用的研究 profile。

此隔离针对 Claude Code 的个人配置，不是操作系统沙箱。项目文件、shell 环境、Claude Code 程序和管理员策略仍然共享。实验工作目录还需要控制可读取文件与项目 skills，固定各组使用的 Claude Code、插件版本和实际模型版本。

## 实验条件

干净的启动环境与 condition 的内容配置分别控制。在已有研究环境中，按实验条件加载所需内容。

Direct 和 Reflection 使用各自的提示，不加载 `autoresearch`。Random Primitives 和 Router Primitives 使用相同的 primitive 集合，区别在选择 primitive 的方式。入口名称、skills 的 descriptions 也属于实验输入，因此 baseline 不加载这个插件。

仓库保存完整 skill 集合。v0 只开放部分 primitives 时，实验提供的插件目录需要只包含该 condition 允许的 skills。直接加载本仓库会开放完整集合。

## 配置依据

环境配置来自 Pi 对话 `01a1174c-91b9-7462-aa5f-cb16781e9bd8`，原始文件为 `/Users/junjie/.pi/agent/sessions/--Users-junjie-config--/2026-10-07T16-57-36-442Z_01a1174c-91b9-7462-aa5f-cb16781e9bd8.jsonl`。

2026-10-08 的记录 `d0dda641` 建立启动器，`3e4705bd` 建立独立 profile，`e8087142` 记录干净 baseline 与临时 skill、plugin 发现检查通过，`273fc7be` 写入 profile 使用说明。本次还读取了当前启动脚本与 profile README。此前检查没有覆盖 hooks 或带共同 protocol 的实验对比，本次只做插件结构校验，没有重跑模型调用。

## 后续 hooks

后续 hooks 放在根目录的 `hooks/hooks.json`，相关脚本放在 `scripts/`。hook 命令通过 `${CLAUDE_PLUGIN_ROOT}` 引用插件内脚本，避免依赖本机路径。

按原始实验设计，第一版 hooks 负责记录和输出验证。具体事件和日志格式在实现时确定。
