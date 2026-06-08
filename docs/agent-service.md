# AgentLight 后台 Agent 服务

AgentLight 的电脑端形态不是桌面 App，而是后台 Agent 服务。服务负责监听本机 AI Agent 状态，并通过现有桥接链路把状态发送到 ESP32-C3。

## 服务形态

| 系统 | 形态 | 运行身份 |
| --- | --- | --- |
| Windows | Windows Service Agent | 系统服务 |
| macOS | LaunchAgent | 当前登录用户 |
| Linux | systemd user service | 当前登录用户 |

Windows 采用 Service Agent，适合后台常驻和开机自启。macOS 采用 LaunchAgent，本质也是后台服务，但运行在当前登录用户身份下，更适合读取 `~/.codex`、`~/.cursor`、`~/.claude` 等用户目录。

## 服务入口

统一入口：

```bash
scripts/agentlight-agent run --config config/agentlight-agent.example.json
```

配置检查：

```bash
scripts/agentlight-agent check-config --config config/agentlight-agent.example.json
scripts/agentlight-agent print-runtime --config config/agentlight-agent.example.json
```

服务入口会启动：

```bash
scripts/multi-agent-monitor --config <monitor-config> --send
```

如果监听器退出，服务入口会按配置自动重启。

## 配置

示例配置：[config/agentlight-agent.example.json](../config/agentlight-agent.example.json)

| 字段 | 说明 |
| --- | --- |
| `monitorConfig` | 多 Agent 监听配置文件 |
| `sendToHardware` | 是否把事件发送到硬件 |
| `pollIntervalSeconds` | 文件监听轮询间隔 |
| `restartDelaySeconds` | 监听器退出后的重启等待时间 |
| `logFile` | 日志文件路径；为空时使用系统默认路径 |
| `environment` | 注入给桥接脚本的环境变量 |

## Windows 安装

以管理员身份打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\service\windows\install-service.ps1
```

默认服务名：

```text
AgentLightAgent
```

默认配置：

```text
%ProgramData%\AgentLight\agentlight-agent.json
```

默认日志：

```text
%ProgramData%\AgentLight\logs\agentlight-agent.log
```

常用命令：

```powershell
Get-Service AgentLightAgent
Start-Service AgentLightAgent
Stop-Service AgentLightAgent
.\service\windows\uninstall-service.ps1
```

## macOS 安装

```bash
service/macos/install-launch-agent.sh
```

默认 plist：

```text
~/Library/LaunchAgents/com.whaleskylabs.agentlight.agent.plist
```

默认配置：

```text
~/.agentlight/agentlight-agent.json
```

默认日志：

```text
~/Library/Logs/AgentLight/
```

常用命令：

```bash
launchctl list | grep whaleskylabs
tail -f ~/Library/Logs/AgentLight/agentlight-agent.log
service/macos/uninstall-launch-agent.sh
```

## 当前边界

- 当前服务默认走 Wi-Fi HTTP 控制 ESP32-C3。
- USB Serial 和 BLE 可以在后续作为传输层扩展接入。
- 服务不提供托盘 UI、Dashboard 或权限气泡。
- 服务只同步可观察到的 AI Agent 状态，权限确认仍由原 AI 工具处理。
