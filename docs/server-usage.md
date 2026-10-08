# 服务器使用说明

## 本地：杭州服务器

在本地终端使用已配置的 SSH 别名连接：

```bash
ssh hangzhou_server
```

首次使用前，需在本机配置 `hangzhou_server` 这个 SSH 别名。

## Remote：优云智算

远程算力使用优云智算 CompShare，CLI 命令为 `compshare`。

首次使用时安装 CLI，并按提示配置账号凭据：

```bash
pip install compshare-cli
compshare config --name default
```

查看实例列表，取得目标实例 ID 后连接：

```bash
compshare --json instance list --all
compshare instance ssh INSTANCE_ID
```

将 `INSTANCE_ID` 替换为实际实例 ID。进入服务器后，在项目目录运行实验。
