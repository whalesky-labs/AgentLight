# AgentLight 使用说明

本文档面向第一次使用 AgentLight 的用户，按实际落地顺序说明硬件接线、固件烧录、设备验证、后台服务启动和 AI 工具接入。

## 使用流程

```text
准备硬件
  -> 接线
  -> 构建并烧录固件
  -> 验证 USB / BLE / Wi-Fi 控制
  -> 配置电脑端 Agent 服务
  -> 启动后台服务
  -> 接入 Codex 或其他 AI 工具
  -> 查看日志和排查问题
```

## 准备硬件

需要准备：

| 物料 | 说明 |
| --- | --- |
| ESP32-C3 SuperMini | 当前固件目标开发板 |
| 玩具红 / 黄 / 绿灯 | 也可以先用普通红黄绿 LED 验证 |
| 220R 电阻 | 每一路灯都需要串联限流 |
| USB 数据线 | 必须支持数据传输，不能只支持充电 |

默认 GPIO：

| 灯 | ESP32-C3 GPIO | 连接方式 |
| --- | --- | --- |
| 红灯 | GPIO4 | GPIO4 -> 220R -> 红灯正极 |
| 黄灯 | GPIO5 | GPIO5 -> 220R -> 黄灯正极 |
| 绿灯 | GPIO6 | GPIO6 -> 220R -> 绿灯正极 |
| 共用负极 | GND | 三路灯负极接 GND |

如果玩具灯是共阳接法，需要把共用正极接到 `3V3`，并在 [platformio.ini](../platformio.ini) 中把 `AGENTLIGHT_ACTIVE_LOW=1`。

## 构建并烧录固件

安装 PlatformIO 后，在仓库根目录执行：

```bash
pio run -e esp32-c3-supermini
pio run -e esp32-c3-supermini -t upload
pio device monitor
```

烧录成功后，固件会同时开启：

| 通道 | 用途 |
| --- | --- |
| USB Serial | 通过串口发送文本命令 |
| Bluetooth LE | 通过 BLE RX 特征写入文本命令 |
| Wi-Fi HTTP | 电脑连接设备 AP 后通过 HTTP API 发送命令 |

默认固件配置：

| 配置 | 默认值 |
| --- | --- |
| BLE 设备名 | `WHALESKY-LABS-AGENTLIGHT` |
| Wi-Fi AP | `WHALESKY-LABS-AGENTLIGHT` |
| Wi-Fi 密码 | `agentlight` |
| HTTP 地址 | `http://192.168.4.1` |

## 验证硬件

### 使用 Wi-Fi HTTP 验证

1. 电脑连接 Wi-Fi：`WHALESKY-LABS-AGENTLIGHT`
2. 密码输入：`agentlight`
3. 执行命令：

```bash
curl "http://192.168.4.1/status"
curl "http://192.168.4.1/command?cmd=GREEN"
curl "http://192.168.4.1/command?cmd=YELLOW_BLINK"
curl "http://192.168.4.1/command?cmd=RED_BLINK"
```

如果灯能按命令切换，说明硬件、固件和 Wi-Fi 控制通道已经可用。

### 使用 USB Serial 验证

打开串口监视器：

```bash
pio device monitor
```

在串口中输入：

```text
GREEN
YELLOW_BLINK
RED_BLINK
STATUS
```

每条命令以换行结尾。成功时固件会返回 `OK <STATE>` 或 `STATUS <STATE>`。

### 使用桥接脚本验证

桥接脚本默认使用 Wi-Fi HTTP：

```bash
scripts/agentlight status
scripts/agentlight green
scripts/agentlight yellow-blink
scripts/agentlight red-blink
```

如果设备地址不是默认值，可以设置：

```bash
export AGENTLIGHT_BASE_URL="http://192.168.4.1"
```

## 启动电脑端后台服务

电脑端后台服务负责监听 AI 工具状态，并把状态事件发送到硬件。

默认配置文件是 [config/agentlight-agent.example.json](../config/agentlight-agent.example.json)：

```json
{
  "activePlatform": "codex",
  "multiSessionMode": "latest-event-wins",
  "sendToHardware": true,
  "environment": {
    "AGENTLIGHT_HOST": "192.168.4.1",
    "AGENTLIGHT_TIMEOUT": "2"
  }
}
```

关键规则：

- 服务启动时只监听一个 `activePlatform`。
- 多会话策略固定为 `latest-event-wins`。
- 同一平台内哪个会话最后产生状态事件，硬件灯就显示哪个会话的状态。
- `sendToHardware=true` 时，事件会继续发送到硬件；测试监听时可以先改成 `false`。

### 前台试运行

先用前台模式确认配置没问题：

```bash
scripts/agentlight-agent check-config --config config/agentlight-agent.example.json
scripts/agentlight-agent print-runtime --config config/agentlight-agent.example.json
scripts/agentlight-agent run --config config/agentlight-agent.example.json --once
```

如果只想看 Codex 状态能否被监听，不控制硬件，可以直接运行：

```bash
scripts/codex-session-monitor --once --limit 20
```

### macOS 后台服务

安装 LaunchAgent：

```bash
service/macos/install-launch-agent.sh
```

默认配置位置：

```text
~/.whalesky-labs-AgentLight/agentlight-agent.json
```

默认日志位置：

```text
~/Library/Logs/whalesky-labs-AgentLight/
```

查看服务：

```bash
launchctl list | grep whalesky-labs
tail -f ~/Library/Logs/whalesky-labs-AgentLight/agentlight-agent.log
tail -f ~/Library/Logs/whalesky-labs-AgentLight/launchagent.err.log
```

卸载：

```bash
service/macos/uninstall-launch-agent.sh
```

### Windows 后台服务

以管理员身份打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\service\windows\install-service.ps1
```

默认服务名：

```text
whalesky-labs-AgentLight
```

默认配置位置：

```text
%ProgramData%\whalesky-labs-AgentLight\agentlight-agent.json
```

默认日志目录：

```text
%ProgramData%\whalesky-labs-AgentLight\logs\
```

常用命令：

```powershell
Get-Service whalesky-labs-AgentLight
Start-Service whalesky-labs-AgentLight
Stop-Service whalesky-labs-AgentLight
.\service\windows\uninstall-service.ps1
```

## 切换 AI 平台

查看当前平台：

```bash
scripts/agentlight-agent platform get --config config/agentlight-agent.example.json
```

查看可用平台：

```bash
scripts/agentlight-agent platform list --config config/agentlight-agent.example.json
```

切换到 Codex：

```bash
scripts/agentlight-agent platform set codex --config config/agentlight-agent.example.json
```

切换平台后，需要重启后台服务，让新平台配置生效。

## 接入 AI 工具

统一事件入口：

```bash
scripts/agentlight-event --agent <agent> --event <event> --send
```

常用事件：

| 事件 | 灯光状态 |
| --- | --- |
| `start` | `YELLOW_BLINK` |
| `tool` | `YELLOW_BLINK` |
| `thinking` | `YELLOW_BREATHE` |
| `done` | `GREEN_BLINK` |
| `waiting` | `RED_BLINK` |
| `error` | `RED` |
| `idle` | `GREEN` |

Codex 推荐先使用本地 session 监听：

```bash
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --from-start
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --event-command scripts/agentlight-event
```

其他平台可以先使用通用 wrapper：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh <agent> <command> "$@"
```

不同平台的具体接入说明见：

- [hooks/agents/README.md](../hooks/agents/README.md)
- [hooks/codex/README.md](../hooks/codex/README.md)
- [hooks/cursor/README.md](../hooks/cursor/README.md)
- [docs/agent-platform-compatibility.md](./agent-platform-compatibility.md)

## 常见问题

### Wi-Fi 连接后没有响应

- 确认电脑连接的是 `WHALESKY-LABS-AGENTLIGHT`。
- 确认请求地址是 `http://192.168.4.1`。
- 确认固件已经烧录成功，并且开发板已重新上电。

### 灯不亮

- 检查每一路灯是否串联 220R 电阻。
- 检查 GPIO 是否对应 `GPIO4`、`GPIO5`、`GPIO6`。
- 检查玩具灯是共阴还是共阳；共阳需要设置 `AGENTLIGHT_ACTIVE_LOW=1`。
- 用 `GREEN`、`YELLOW_BLINK`、`RED_BLINK` 分别测试三路。

### 服务启动了但灯没有变化

- 先运行 `scripts/agentlight yellow-blink`，确认硬件通道可用。
- 查看服务配置中的 `sendToHardware` 是否为 `true`。
- 查看 `AGENTLIGHT_HOST` 或 `AGENTLIGHT_BASE_URL` 是否指向正确设备。
- 查看后台服务日志，确认监听器是否有事件输出。

### Codex 状态没有被监听到

- 确认 Codex 已经产生本地 session JSONL。
- 先运行 `scripts/codex-session-monitor --once --limit 20` 看是否有输出。
- 如果要限制到某个会话，确认 `CODEX_THREAD_ID` 是否正确。

## 项目边界

AgentLight 只负责把可观察到的 AI Agent 状态同步到硬件红黄绿灯。

当前不提供：

- 桌面 GUI 客户端
- 托盘面板
- Dashboard
- 权限气泡
- 终端聚焦
- 自动改写第三方 AI 工具配置
