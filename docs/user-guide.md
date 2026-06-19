# AgentLight 使用说明

本文档面向第一次使用 AgentLight 的用户，按实际落地顺序说明硬件接线、固件烧录、设备验证、微信消息服务启动和排查问题。

## 使用流程

```text
准备硬件
  -> 接线
  -> 构建并烧录固件
  -> 验证 USB / BLE / Wi-Fi 控制
  -> 配置微信消息服务
  -> 启动后台服务
  -> 收到微信消息时验收灯效
  -> 查看日志和排查问题
```

## 准备硬件

| 物料 | 说明 |
| --- | --- |
| ESP32-C3 SuperMini | 当前固件目标开发板 |
| BS-768 玩具红绿灯小板 | 拆掉原控制 / 限流元件后，只保留灯珠和走线 |
| 220R 电阻 | 每一路 GPIO 到灯珠控制脚都需要单独串联 |
| USB 数据线 | 必须支持数据传输，不能只支持充电 |

默认接线：

![AgentLight 接线图](./assets/agentlight-wiring.svg)

| 连接点 | ESP32-C3 引脚 | 接法 |
| --- | --- | --- |
| 公共正极 | 3V3 | `3V3` -> 小板公共 `+` |
| 公共负极 | GND | `GND` -> 小板 `-` |
| 红灯控制端 | GPIO4 | `GPIO4` -> 220R -> 红灯控制脚 |
| 黄灯控制端 | GPIO5 | `GPIO5` -> 220R -> 黄灯控制脚 |
| 绿灯控制端 | GPIO6 | `GPIO6` -> 220R -> 绿灯控制脚 |

BS-768 小板按共阳方式控制，固件默认已经设置 `AGENTLIGHT_ACTIVE_LOW=1`。GPIO 拉低时对应灯亮，GPIO 拉高时对应灯灭。

## 构建并烧录固件

安装 PlatformIO 后，在仓库根目录执行：

```bash
pio run -e esp32-c3-supermini
pio run -e esp32-c3-supermini -t upload
pio device monitor
```

默认固件配置：

| 配置 | 默认值 |
| --- | --- |
| BLE 设备名 | `WHALESKY-LABS-AGENTLIGHT` |
| BLE 广播短名称 | `AGENTLIGHT` |
| BLE 配对码 | `123456` |
| Wi-Fi AP | `WHALESKY-LABS-AGENTLIGHT` |
| Wi-Fi 密码 | `12345678` |
| HTTP 地址 | `http://192.168.4.1` |

## 验证硬件

### USB Serial

```bash
scripts/agentlight status
scripts/agentlight green
scripts/agentlight yellow-blink
scripts/agentlight red-blink
scripts/agentlight all
```

### Wi-Fi HTTP

1. 电脑连接 Wi-Fi：`WHALESKY-LABS-AGENTLIGHT`
2. 密码输入：`12345678`
3. 执行命令：

```bash
AGENTLIGHT_TRANSPORT=http AGENTLIGHT_BASE_URL=http://192.168.4.1 scripts/agentlight status
AGENTLIGHT_TRANSPORT=http AGENTLIGHT_BASE_URL=http://192.168.4.1 scripts/agentlight yellow-blink
```

### BLE

BLE 只使用系统已经连接的设备，不主动扫描、连接或重连。

```bash
AGENTLIGHT_TRANSPORT=ble-system scripts/agentlight status
AGENTLIGHT_TRANSPORT=ble-system scripts/agentlight yellow-blink
```

如果系统蓝牙没有连接 `AGENTLIGHT`，命令会返回 `SKIP BLE_NOT_CONNECTED`。需要重新连接时，长按 ESP32-C3 板载 `BOOT` 键 2 秒打开 60 秒手动连接窗口，再从系统蓝牙里点击连接。

## 微信消息服务

示例配置：

```text
config/wechat-agentlight.example.json
```

安装用户配置：

```bash
scripts/agentlight-wechat install-config
```

默认用户配置路径：

| 系统 | 路径 |
| --- | --- |
| macOS | `~/.whalesky-labs-AgentLight/wechat-agentlight.json` |
| Windows | `%APPDATA%\whalesky-labs-AgentLight\wechat-agentlight.json` |

前台检查：

```bash
scripts/agentlight-wechat check-config
scripts/agentlight-wechat print-runtime
scripts/agentlight-wechat doctor
```

前台运行一次：

```bash
scripts/agentlight-wechat once
```

持续运行：

```bash
scripts/agentlight-wechat run
```

## 事件和灯效

| 微信事件 | 灯效 |
| --- | --- |
| `wechat-message` | 黄灯闪烁 |
| `wechat-important` | 红灯闪烁 |
| `wechat-muted` | 不改变当前灯效 |
| `wechat-cleared` | 全灭 |
| `wechat-offline` | 全灭 |
| `wechat-listener-error` | 红灯常亮 |

默认清除策略是 `timeout-or-unread-cleared`，300 秒内如果监听器能观察到未读消失则熄灯，否则超时熄灯。

## macOS 微信监听

macOS helper 使用 Accessibility API 观察微信进程、窗口标题、可见未读状态和可见摘要。

需要在系统设置中给运行环境授予辅助功能权限。权限缺失时：

```bash
scripts/agentlight-wechat doctor
```

会输出 Accessibility 诊断。微信版本或 UI 结构导致联系人、群名、摘要不可读时，服务会降级为普通未读提醒。

## Windows 微信监听

Windows helper 使用 UI Automation 观察微信窗口的可见未读状态和可见摘要。

如果微信窗口不可读或 UI Automation 不可用，`doctor` 会输出明确诊断。

## 后台服务

### macOS

```bash
service/macos/install-launch-agent.sh
```

日志目录：

```text
~/Library/Logs/whalesky-labs-AgentLight/
```

查看：

```bash
launchctl list | grep whalesky-labs
tail -f ~/Library/Logs/whalesky-labs-AgentLight/agentlight-wechat.log
tail -f ~/Library/Logs/whalesky-labs-AgentLight/launchagent.err.log
```

卸载：

```bash
service/macos/uninstall-launch-agent.sh
```

### Windows

以管理员身份打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\service\windows\install-service.ps1
```

常用命令：

```powershell
Get-Service whalesky-labs-AgentLight
Start-Service whalesky-labs-AgentLight
Stop-Service whalesky-labs-AgentLight
.\service\windows\uninstall-service.ps1
```

## 不依赖微信的本地链路测试

fake helper 可以验证事件 -> 规则 -> 状态机 -> 下发链路：

```bash
python3 - <<'PY'
import json
from pathlib import Path

config = json.loads(Path("config/wechat-agentlight.example.json").read_text())
config["sendToHardware"] = False
config["helperCommand"] = ["scripts/agentlight-wechat-fake-helper", "message"]
Path("/tmp/wechat-agentlight-test.json").write_text(json.dumps(config))
PY

scripts/agentlight-wechat once --config /tmp/wechat-agentlight-test.json
```

预期输出包含：

```text
event=wechat-message
state=unread
command=YELLOW_BLINK
```

## 常见问题

### 灯不亮

- 检查 `3V3` 是否接到小板公共 `+`，`GND` 是否接到小板 `-`。
- 检查 GPIO 到每一路灯珠控制脚之间是否串联了 220R。
- 用 `scripts/agentlight all` 进行全亮自检。
- 用 `scripts/agentlight green`、`yellow-blink`、`red-blink` 分别测试三路。

### 微信收到消息但灯没有变化

- 先运行 `scripts/agentlight yellow-blink`，确认硬件通道可用。
- 运行 `scripts/agentlight-wechat doctor`，查看微信进程、权限和 helper 状态。
- 查看配置中的 `sendToHardware` 是否为 `true`。
- macOS 检查 Accessibility 权限。
- Windows 检查微信窗口是否可被 UI Automation 读取。

### 日志里看不到消息内容

这是默认隐私策略。普通日志只记录事件类型、平台、命中规则、状态和硬件命令，不保存消息正文、发送人或会话名。

## 项目边界

AgentLight 只负责把本机可观察到的个人微信桌面消息状态同步到硬件红黄绿灯。

当前不提供：

- 微信自动回复
- 微信机器人
- 微信进程注入
- 微信数据库解密
- 完整聊天历史读取
- 桌面 GUI 客户端
