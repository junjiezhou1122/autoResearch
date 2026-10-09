# 路由执行与仓库整理

日期为 2026-10-09，工作会话为 `6f2792f5-802a-49a7-a376-78c1abd74ffa`。用户要求更新 skill、整理仓库、不提交实验数据，并将进度和其他源码提交一版。

## 入口变更

AI Idea 接入纠正后的三次 Skills 运行识别了入口，但没有研究 leaf 工具调用。注册清单含 `Skill` 和全部 leaf，轨迹未发现权限阻塞。保存的事件不足以证明完整技能描述与入口正文实际如何传给模型，思考文本也未解释跳过的原因，因此具体原因未定。

旧轮要求选好操作后加载对应 skill，三题共 15 次 leaf 调用。新旧冻结插件的 16 个 SKILL.md 内容完全一致，任务提示与通用说明发生了变化。这个比较提示执行指令可能影响路由，但不构成因果验证。

ask-matt 主要提供情境与流程导航。poteto-mode 还要求按触发条件加载技能、读取 playbook 并执行。当前 research-mode 采用简短的选择与执行规则，通过 `Skill` 加载所选 leaf，把输出作为中间工作，按研究状态继续直到原任务交付。入口保留用户显式调用设置，15 个 leaf 不变。通用 agent 说明同步明确加载动作。插件版本改为 0.1.1。

新入口尚未进行模型复测。此次只做 frontmatter、路由链接、插件结构与 Git 保存范围检查，不将历史实验分数归到新版，也不宣称已经改善调用率。

## Git 保存范围

提交插件元数据和 skills、文档、`scripts/` 源码、`experiments/` 方案、`progress/` 记录，以及已有来源和许可证的 `.claude/skills/` benchmark 接入技能。

忽略本地 `results/`、`decisions.tsv`、`todo.md`、Python 缓存、环境与 secret 文件、本机客户端 hooks 配置和 Entire 会话捕获。所有现有实验数据保留在原位置。文档中的 `results/` 链接需要本地数据，普通 clone 不包含这些产物。

Entire 项目接入配置留在本地，现有 Git hooks 保留。提交前确认 telemetry 与 push_sessions 均关闭。Git 提交可能在本机创建 checkpoint，但没有上传或推送会话。本文记录整理边界，不将客户端 hooks 称为研究插件 hooks。

## 实验进度

ResearchBench 的单次 API、原生运行、入口全量重跑及单题完成复测见[历史会话记录](2026-10-08-research-skills.md)。另外五项 benchmark 的范围、未完成评分与人为 ResearchClaw 截止限制见[五项记录](2026-10-09-other-benchmarks.md)。AI Idea 的九份完整字段输出、27 次有效最终评分、零 leaf 调用及全文输入差异见[AI Idea 重跑记录](2026-10-09-ai-idea-rerun.md)。[实验记录](../docs/experiments.md)保存各轮结果，不能用生成成功替代质量评估完成。

## 验证与提交

本地整理位于 `chore/research-routing-and-repo-cleanup` 分支。插件结构校验通过，唯一警告是根目录 CLAUDE.md 不随插件自动加载，已有文档说明显式加载方式。16 个 skill 的 frontmatter 与路由链接有效，15 个 leaf 与原提交一致，13 个 Python 源码通过语法解析。Git index 未包含实验输出、客户端会话、缓存或工作日志；113 个仓库文档链接和 34 个本地结果链接已检查。没有启动新模型实验或推送。

源码审阅最初标记了三处本地 bearer 值，主会话核对后确认均为占位认证 `magpie`，不是 provider secret，已在 scripts README 解释。历史 IGI 保存键交换是官方布局，未作为 bug 修复。源码依赖外部 checkout 与人工审计，不能称为普通 clone 后一键复现。

Laziness Protocol 决定只改入口执行关系与存储边界，不扩写 leaf 或重构历史 runners。Prove It Works 决定检查实际 index、插件结构与原 leaf 内容。源码与最终提交范围审阅实际报告路由均为 `group/auto-gpt-6-1-sol[1m]`，不宣称跨模型家族审阅。最终审阅未发现提交阻塞，核对了来源哈希、文档链接、忽略规则和历史版本标记；它没有重新核验科学评分或执行新版模型任务。注释检查没有修改源码。
