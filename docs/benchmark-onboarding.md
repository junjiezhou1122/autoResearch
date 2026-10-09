# 将新的 benchmark 接入 Harbor

以后接入新的 benchmark，使用 `create-adapter` 创建骨架，再按官方指南实现转换、下载数据、验证并交付一键运行入口。用 `harbor-adapter-creator` 补充实现与排错参考。每个 benchmark 的交付都按本流程验收。

本页定义后续接入流程。研究 agent 的任务输入、通用配置、结果收集和评分职责遵循[研究 agent 接入约定](agent-benchmark-contract.md)。现有六个 benchmark 的本地入口和准备状态见 [benchmark 总览](benchmarks.md)。这些本地入口不代表已经完成 Harbor 转换。

## 发起接入任务

提供 benchmark 仓库地址，并使用下面的指令。已知的数据 split、模型、任务范围和调用预算也一起提供。

```text
用 create-adapter，把这个 benchmark repo 适配到 Harbor，下载数据并验证，留下一键运行入口。
按 docs/benchmark-onboarding.md 执行，先完成本地接入和验收。
仓库地址：<benchmark repo URL>
```

先从上游仓库确认 benchmark 名称、数据来源、参考答案和 agent 场景。只有仓库无法确定、且会改变接入结果的选择才向用户确认。未指定正式评测模型和预算时，先完成不需要付费模型的转换与验证，并记录剩余验证项。

## 1. 准备技能、官方指南和环境

本仓库已包含两份项目技能，进入仓库启动新的 Claude Code 会话后，确认能识别到它们。

- [create-adapter](../.claude/skills/create-adapter/SKILL.md) 提供脚手架与官方指南入口。
- [harbor-adapter-creator](../.claude/skills/harbor-adapter-creator/SKILL.md) 提供实现参考，附带 [adapter anatomy](../.claude/skills/harbor-adapter-creator/references/adapter-anatomy.md)。

两份技能位于 `.claude/skills/`，均为可随仓库复制的实际文件。根目录 `skills/` 仍是科研实验插件的 16 个技能。正式实验从独立工作目录启动，不加载这两份接入技能。

[sources.json](../.claude/skills/sources.json) 保存官方仓库、commit、子目录、许可证和文件 SHA-256。每个技能目录都附带上游 Apache-2.0 许可证。

Skills Manager 的中央技能库仍保留官方 Git 来源。使用 `sm skills update create-adapter` 和 `sm skills update harbor-adapter-creator` 更新中央副本后，再核对版本差异，将技能全文、参考文件和许可证同步到仓库，并更新 `sources.json`。`sm` 不会自动更新本仓库的固定副本，也不会同时下载完整的 adapters 仓库。

单独准备官方 `harbor-framework/adapters` 仓库。在仓库根目录完整读取 `docs/adapters.mdx`，再执行脚手架和实现步骤。没有这份指南时，先获取官方仓库，不能用技能摘要替代指南。

记录 adapters 仓库的 origin、commit 和指南路径。检查工作区后获取上游更新；只在工作区允许时更新 checkout，已有本地改动使用独立工作区保留。

确认 Harbor CLI 可用，并检查当前命令帮助。

```bash
harbor --version
harbor --help
harbor adapter --help
```

`create-adapter` 使用单数 `harbor adapter init`，目标目录为 `src/<adapter-name>/`。`harbor-adapter-creator` 含有旧版复数 `harbor adapters init` 和 `adapters/<adapter-id>/` 示例。命令与布局有差异时，以当前官方 `docs/adapters.mdx` 和已安装 CLI 的帮助为准。若 CLI 与指南不兼容，先对齐版本。

将接入操作放在准备环境中。正式受控实验只加载该 condition 允许的研究技能与工具，不能因为接入时使用了 Harbor 技能就扩大实验权限。

## 2. 固定上游与评测范围

在对应 benchmark 的操作文档中记录以下信息。

- 上游仓库、commit、数据来源、数据 revision、许可证和引用。
- 使用的 split、任务数、原始 task ID，以及确定性的选择顺序或抽样种子。
- agent 可见的输入、必须交付的输出、官方评分方式和失败处理。
- 原始运行环境、附件、联网要求、超时和资源需求。
- 参考答案是否可用，以及是否需要自定义 agent 或上游兼容改造。

先检查官方已有 adapter 是否覆盖目标版本和 split。能复用时，固定版本并验证覆盖范围；需要新 adapter 时，再创建骨架。

保留官方评分定义和数据切分。官方 evaluator 不可获取时，明确标记本地替代评分器及差异。参考答案、隐藏测试、未来论文和真实胜负标签不能进入生成 agent 的可见输入。

## 3. 下载并固定数据

把每个新下载的数据包和解压内容放入各自新建的空目录。下载与转换脚本放在独立的代码目录，通过参数读取数据路径。使用 Python 读取下载内容时加 `-I`。

保留原始数据，另存转换结果。保存下载来源、revision、文件校验和、下载完成状态和最终任务清单。数据不完整、附件缺失或许可证不允许使用时，报告阻塞项。

让准备入口复用已验证的数据缓存。数据来源或版本发生变化时重新校验，不能把旧缓存当作新版本。重复运行不覆盖原始数据、已有配置或实验结果。

## 4. 创建并实现 adapter

在官方 adapters 仓库的独立分支或工作区操作。名称已确定时，按 `create-adapter` 使用非交互脚手架。

```bash
harbor adapter init <adapter-name> --name "<Human-Readable Name>"
```

按官方指南核对生成目录，并实现数据转换、任务模板、环境、verifier 和 oracle。新接入采用指南要求的目录结构，不把旧技能中的目录结构拼入新骨架。

生成任务时使用稳定、唯一的名称，保留原始 task ID 到 Harbor task ID 的映射。在每个 `task.toml` 的 `[task]` 下填写 `name`，格式为 `<org>/<task-name>`。保持 schema 的 `version = "1.0"`，dataset 版本采用发布标签。让 `main.py` 支持 `--output-dir`、`--limit`、`--overwrite` 和 `--task-ids`。

让 verifier 输出 Harbor 要求的 reward，并保留原始评分证据。把执行异常、输出缺失和评分失败分别记录，不能静默丢弃失败任务。

按官方模板填写 adapter 的 README 和元数据。README 会被自动解析，保留模板规定的章节和顺序，补充内容放入指定的 Notes 区域。所有 schema 和必填字段均以本次固定的官方指南为准。

## 5. 分层验证接入结果

按下面的顺序验收。实际命令从当前 CLI 帮助和官方指南取得，并写入该 benchmark 的操作文档。

1. 检查依赖、数据完整性、任务数和 ID 映射。用同一输入重复转换，核对任务名称和内容是否一致。
2. 执行 adapter 结构与 schema 校验，再检查生成任务。处理残留模板占位符、缺失附件和 reward 写入问题。
3. 选取小范围任务，验证环境构建、执行、输出收集和 verifier。固定样本范围后再扩大验证。
4. 使用已有参考解运行 oracle。按官方指南验证全部目标任务，并要求全部任务获得 100% reward。未通过时保留逐题错误，核对上游参考解、环境和转换逻辑；无法修复的任务须明确记录排除原因和调整后的任务范围。
5. 对缺失输出和已知错误输出运行 verifier，确认错误没有被误记为通过。
6. 运行一键入口，确认结果目录、日志、任务分母和失败记录完整。

把 fixture、回放、结构校验、oracle 和真实模型运行分别标记。fixture 成功只证明流程能执行。oracle 成功证明参考解可以通过当前环境与评分器，不能代替真实模型评测或 parity。

若 oracle 需要模型生成参考解，或 verifier 需要付费 judge，先确认已有模型与费用授权。不能执行的验证项注明原因，不能报告为通过。

## 6. 交付一键运行入口

每个接入完成的 benchmark 都交付下列文件与行为。

- 提供准备入口，完成依赖检查、缓存校验和任务转换。首次运行下载数据，后续复用同一版本的数据。
- 提供无需付费模型的检查入口。需要付费 judge 的检查另行标明。
- 提供正式运行入口，通过配置文件指定 agent、模型、任务子集、预算、并发和所需评分服务。
- 提供不含凭据的配置模板。真实凭据通过环境变量或未提交的本地配置注入。
- 每次实验创建新的结果目录，保存配置、版本、任务清单、原始输出、reward、用量和失败记录。结束时打印结果路径。
- 在本项目的 `docs/benchmarks/<benchmark>.md` 写出已验证的完整命令、预期输出、结果位置和复跑方法，并更新 [benchmark 总览](benchmarks.md)。

实现时优先复用现有 `bench.sh` 与 `experiment.sh` 的操作方式，或提供对应 Harbor job 配置和包装入口。让使用者只需选择 benchmark 和配置文件，就能开始运行。

按官方指南提供 `run_<adapter-name>.yaml`，默认使用 oracle，并支持单独的正式实验配置。指南中的本地配置入口如下，具体数据路径与 agent 配置需在接入时填入并验证。

```bash
harbor run -c src/<adapter-name>/run_<adapter-name>.yaml
```

发布前使用本地路径和配置运行。只有 dataset 发布后，才使用 registry 的 `-d <org>/<dataset>@<tag>` 入口。

入口命令以该次实际交付为准。本页不预设尚未实现的 Harbor 包装脚本。验收时亲自执行所写命令，并说明验证使用 fixture、oracle 还是真实 agent。

## 7. 按实验授权执行 parity 与发布

需要确认 Harbor 结果与原 benchmark 一致时，再安排 parity。先固定两边相同的任务、agent、模型、提示、预算和重复次数，并保留两边的原始结果。评分指标与匹配条件采用官方指南，不能自行放宽条件。

按官方流程提交 adapter 时，在 parity 前完成 Harbor 团队协调；对外联系按用户授权执行。依次完成两边的小范围检查、两边各一次完整运行，再扩展重复次数。按指南报告每次原始分数、均值和 sample SEM。完成本地接入后若未证明 parity，不能宣称与上游结果可直接比较。

正式模型评测、付费 judge 和 parity 按用户已授权的范围与预算执行。未授权时先交付本地 adapter、数据、检查证据和运行入口。将 parity 状态记为未运行。

注册 dataset、提交外部 PR 和上传结果属于后续发布步骤。按明确的发布请求执行，并采用本次官方指南的注册流程。

## 验收并记录状态

在该 benchmark 文档末尾填写以下清单。未完成项保留原因。

- [ ] 已固定上游、数据、adapter 和 Harbor 版本。
- [ ] 已保存数据校验和、目标任务清单和 ID 映射。
- [ ] adapter 与任务校验通过。
- [ ] 小范围运行通过，错误输出验证完成。
- [ ] 全部目标任务的 oracle 验证完成，逐题结果可查。
- [ ] 一键入口已实际执行，重复运行复用缓存并创建新结果目录。
- [ ] 配置模板、完整运行命令和结果读取方法已写入文档。
- [ ] 真实模型评测、parity 和发布各自注明完成或未运行。

2026-10-08 本次交付为接入流程文档，没有新建 Harbor adapter、下载新 benchmark 或运行 Harbor 验证。当前环境未发现可用的 Harbor CLI，接入时需先安装或配置。具体 benchmark 的接入状态以其操作文档和运行证据为准。

本次核对的官方指南位于 `/Users/junjie/.skills-manager/cache/repos/d92d31c0dd364ee1/docs/adapters.mdx`。该 checkout 的 origin 为 `harbor-framework/adapters`，commit 为 `68226cfa22d996a925c3969966a6aaab64249d46`。这是本次核对记录，缓存路径可能变化，也未检查远程是否有新提交；后续每次接入都重新确认指南和 CLI 版本。
