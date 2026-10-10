# 为 autoResearch 接入 Entire

在仓库的 Git 工作目录中接入 Entire，记录日常 AI 开发会话，并在提交代码时关联 checkpoint。本文命令按官方 CLI `0.11.4` 核对。

## 启用本地记录

先确认已安装 CLI。新机器可用官方 Homebrew 包安装。

```bash
brew install --cask entireio/tap/entire
entire version
```

进入 autoResearch 的 Git 工作目录后执行以下命令。已安装的机器跳过安装步骤。

```bash
entire enable --agent claude-code --project --telemetry=false \
	--skip-push-sessions --absolute-git-hook-path --no-init-repo
entire agent add codex
entire agent add cursor
entire agent add factoryai-droid
entire agent add opencode
entire agent add pi
```

只使用部分客户端时，只添加对应客户端。Git hooks 是本地文件，不随 clone 分发。新 clone 仍需运行 `entire enable` 安装 hooks。

项目配置位于 `.entire/settings.json`，当前为 `enabled=true`、`telemetry=false`、`strategy_options.push_sessions=false`、`absolute_git_hook_path=true`，checkpoint 存储类型为 `git-refs`。本地 checkpoint 位于 `refs/entire/checkpoints/`，不进入当前分支的代码提交历史。代码提交通过 `Entire-Checkpoint` trailer 关联 checkpoint。

保留关闭会话自动上传的设置。不要在接入时导入历史、开启自动 AI 摘要，或安装可选 search、agent-help skills。当前接入未启用这些功能。

## 检查客户端接入

执行以下只读命令检查配置和已登记的会话。

```bash
entire status
entire status --detailed
entire agent list
entire sessions list --json
```

当前已安装六个客户端的 hooks 或扩展，文件分别位于：

- Claude Code 的 `.claude/settings.json`。
- Codex 的 `.codex/hooks.json`。
- Cursor 的 `.cursor/hooks.json`。
- Factory AI Droid 的 `.factory/settings.json`。
- OpenCode 的 `.opencode/plugins/entire.ts`。
- Pi 的 `.pi/extensions/entire/index.ts`。

Codex CLI `0.160.1` 仍需在 Codex 中打开 `/hooks`，审批 7 个 hooks。完成审批前，不要把 Codex 标记为可运行。其他客户端已安装 hooks，但尚未验证完整模型回合。Claude 当前真实会话已通过官方 hook 管道手动登记，本次登记未调用付费模型，也未创建代码提交；这只能证明会话登记，不能证明完整 checkpoint 流程。

## 登录并连接已有镜像

需要访问 Entire 镜像时，选择一种官方登录方式。

```bash
entire auth login
```

无本地浏览器时使用设备登录。`entire login --device` 是等价入口。

```bash
entire auth login --device
```

本仓库的镜像已就绪，位于美国的 `aws-us-east-2.entire.io`。浏览入口为 [autoResearch 的 Entire 页面](https://entire.io/gh/junjiezhou1122/autoResearch)。在新 clone 中，添加独立的 `entire` remote。

```bash
entire repo remote add entire /gh/junjiezhou1122/autoResearch \
	--cluster aws-us-east-2.entire.io
```

`origin` 保留 GitHub。新增 remote 的地址为 `entire://aws-us-east-2.entire.io/gh/junjiezhou1122/autoresearch`。如果 `entire` 已存在，先检查地址，不要重复添加或覆盖。

```bash
git remote -v
git ls-remote entire HEAD refs/heads/main
```

本次接入核验中，镜像的 `HEAD` 和 `refs/heads/main` 均为 `d536d783295c0cd9ccec023e7268d882c2cc7305`。后续提交可能改变该值；检查时以实际输出为准。

镜像就绪不代表会话已发布。本仓库是公开仓库，上传到公开仓库的会话 transcript 会公开。发布会话需要单独明确批准。自动脱敏不能代替发布前检查，也不要手动推送会话的临时 shadow branches。

## 日常检查与停用

本机 OpenCLI 已注册官方 Entire CLI，无需自定义网页 adapter。以下命令已实际验证登录、agent 列表和镜像状态。注册信息位于 `~/.opencli/external-clis.yaml`。

```bash
opencli entire auth status
opencli entire agent list
opencli entire repo view /gh/junjiezhou1122/autoResearch --json
```

查看当前分支的本地 checkpoint。

```bash
entire checkpoint list
git for-each-ref refs/entire/checkpoints
```

要停用当前仓库的 Entire，执行以下命令。hooks 保留但不再工作；该命令不注销账户，也不删除历史。

```bash
entire disable
```

## 保持受控实验隔离

不要为捕获实验会话而修改 runner 的工作目录、settings 或持久化选项。本地历史 runner `experiments/scripts/run_runtime_pilot.py` 在临时非 Git 目录运行 `claude-research`。该 launcher 仅加载用户 settings，runner 使用 `--no-session-persistence`，不会加载本仓库的项目 hooks。直接调用 API 的 runners 也不经过客户端 hooks。实验脚本不随 GitHub 仓库分发。

继续以 `experiments/results/` 中的原始请求、输出、用量和评分文件作为实验记录。Entire 记录用于仓库开发追踪，不能代替实验产物，也不提供完整实验捕获。接入 Entire 不改变实验条件、允许的证据、工具预算或 primitive 调用规则。
