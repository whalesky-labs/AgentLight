# AgentLight 后台 Agent 服务

AgentLight 的电脑端形态不是桌面 App，而是后台 Agent 服务。服务负责监听本机 AI Agent 状态，并通过现有桥接链路把状态发送到 ESP32-C3。

## 服务形态

| 系统 | 形态 | 运行身份 |
| --- | --- | --- |
| Windows | Windows Service Agent | 系统服务 |
| macOS | LaunchAgent | 当前登录用户 |
| Linux | systemd user service | 当前登录用户 |

Windows 采用 Service Agent，适合后台常驻和开机自启。macOS 采用 LaunchAgent，本质也是后台服务，但运行在当前登录用户身份下，更适合读取 `~/.codex`、`~/.cursor`、`~/.claude` 等用户目录。

对外暴露的服务名、LaunchAgent label、配置目录和日志目录统一带组织名与项目名，避免和用户机器上已有服务冲突。

## 服务入口

统一入口：

```bash
scripts/agentlight-agent run --config config/agentlight-agent.example.json
```

配置检查：

```bash
scripts/agentlight-agent check-config --config config/agentlight-agent.example.json
scripts/agentlight-agent print-runtime --config config/agentlight-agent.example.json
scripts/agentlight-agent platform get --config config/agentlight-agent.example.json
scripts/agentlight-agent platform list --config config/agentlight-agent.example.json
scripts/agentlight-agent platform set codex --config config/agentlight-agent.example.json
```

服务入口会启动：

```bash
scripts/multi-agent-monitor --config <monitor-config> --platform <activePlatform> --send
```

如果监听器退出，服务入口会按配置自动重启。

## 平台与多会话策略

服务一次只监听一个平台，由 `activePlatform` 指定。这样可以避免 Codex、Claude Code、Cursor 等多个平台同时抢占同一组红绿灯。

同一平台内部允许多项目、多会话同时工作，但不做聚合、不做轮播、不固定单会话。当前策略是 `latest-event-wins`：

```text
A 会话 working  -> 灯显示 A 的工作状态
B 会话 done     -> B 的事件到达后立即替换当前灯光
C 会话 thinking -> C 的事件到达后立即替换当前灯光
```

也就是说，服务会记录并转发当前平台下所有会话事件，但灯光永远显示“最后发生状态变化的会话”。

## 配置

示例配置：[config/agentlight-agent.example.json](../config/agentlight-agent.example.json)

| 字段 | 说明 |
| --- | --- |
| `activePlatform` | 当前服务监听的平台，例如 `codex` |
| `multiSessionMode` | 当前平台内多会话策略；现阶段固定为 `latest-event-wins` |
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
whalesky-labs-AgentLight
```

默认配置：

```text
%ProgramData%\whalesky-labs-AgentLight\agentlight-agent.json
```

默认日志：

```text
%ProgramData%\whalesky-labs-AgentLight\logs\agentlight-agent.log
```

常用命令：

```powershell
Get-Service whalesky-labs-AgentLight
Start-Service whalesky-labs-AgentLight
Stop-Service whalesky-labs-AgentLight
.\service\windows\uninstall-service.ps1
```

## macOS 安装

```bash
service/macos/install-launch-agent.sh
```

默认 plist：

```text
~/Library/LaunchAgents/com.whalesky-labs.AgentLight.agent.plist
```

默认配置：

```text
~/.whalesky-labs-AgentLight/agentlight-agent.json
```

默认日志：

```text
~/Library/Logs/whalesky-labs-AgentLight/
```

常用命令：

```bash
launchctl list | grep whalesky-labs
tail -f ~/Library/Logs/whalesky-labs-AgentLight/agentlight-agent.log
service/macos/uninstall-launch-agent.sh
```

## 当前边界

- 当前服务默认走 Wi-Fi HTTP 控制 ESP32-C3。
- USB Serial 和 BLE 可以在后续作为传输层扩展接入。
- 服务不提供托盘 UI、Dashboard 或权限气泡。
- 服务只同步可观察到的 AI Agent 状态，权限确认仍由原 AI 工具处理。
