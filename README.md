<p align="center">
  <img src="https://avatars.githubusercontent.com/u/277389313?s=200&v=4" width="128" height="128" alt="AgentLight">
</p>

<h1 align="center">微信消息指示灯 · AgentLight</h1>

<p align="center">
  基于 ESP32-C3 的个人桌面微信消息红黄绿灯。
</p>

<p align="center">
  微信消息监听 · USB 串口控制 · Bluetooth LE 控制 · Wi-Fi HTTP 控制
</p>

[简体中文](./README.md) | [English](./README.en.md)

# AgentLight

AgentLight 是一个基于 ESP32-C3 的个人微信桌面消息指示灯项目。电脑端服务监听 macOS / Windows 桌面微信的可观察消息信号，将群消息、好友消息、其他消息、已读清空、离线和监听异常映射为红 / 黄 / 绿三路并发灯效，再通过 USB、系统蓝牙或 Wi-Fi HTTP 下发到硬件。

当前仓库包含：

- **ESP32-C3 固件**：接收灯光命令并控制红 / 黄 / 绿灯。
- **硬件命令桥**：`scripts/agentlight` 通过 USB、BLE 或 HTTP 向设备发送命令。
- **微信消息服务**：`scripts/agentlight-wechat` 运行本机微信监听 helper、规则引擎和灯效状态机。
- **macOS / Windows helper**：各自负责观察本机微信状态并输出统一 JSONL 事件。

完整使用说明见 [docs/user-guide.md](./docs/user-guide.md)。

## 硬件

- ESP32-C3 SuperMini
- BS-768 玩具红 / 黄 / 绿灯小板
- 每一路灯珠控制线单独串联 220R 电阻

默认接线：

![AgentLight 接线图](./docs/assets/agentlight-wiring.svg)

| 连接点 | ESP32-C3 引脚 | 接法 |
| --- | --- | --- |
| 公共正极 | 3V3 | `3V3` -> 小板公共 `+` |
| 公共负极 | GND | `GND` -> 小板 `-` |
| 红灯控制端 | GPIO4 | `GPIO4` -> 220R -> 红灯控制脚 |
| 黄灯控制端 | GPIO5 | `GPIO5` -> 220R -> 黄灯控制脚 |
| 绿灯控制端 | GPIO6 | `GPIO6` -> 220R -> 绿灯控制脚 |

## 固件命令

命令协议使用纯文本，一次发送一条命令：

| 命令 | 结果 |
| --- | --- |
| `GREEN` | 绿灯亮 |
| `YELLOW_BLINK` | 黄灯闪烁 |
| `RED_BLINK` | 红灯闪烁 |
| `LANES:RED=OFF,YELLOW=BLINK,GREEN=BREATHE` | 红 / 黄 / 绿三路独立效果 |
| `RED` | 红灯常亮 |
| `OFF` | 全部熄灭 |
| `ALL` | 红 / 黄 / 绿三路同时常亮 |
| `PING` | 返回 `PONG` |
| `STATUS` | 返回当前灯光状态 |

完整命令还包括 `GREEN_BREATHE`、`GREEN_BLINK`、`YELLOW`、`YELLOW_BREATHE`、`RED_BREATHE`、`ALL_BLINK`、`ALL_BREATHE`、`LANES:RED=OFF,YELLOW=BLINK,GREEN=BREATHE` 和 `HELP`。

## 硬件命令桥

```bash
scripts/agentlight status
scripts/agentlight green
scripts/agentlight wechat-group-new
scripts/agentlight wechat-friend-new
scripts/agentlight wechat-other-new
```

默认 `AGENTLIGHT_TRANSPORT=auto`：检测到 USB 串口时走 USB；没有 USB 串口时走系统蓝牙。也可以显式指定：

```bash
AGENTLIGHT_TRANSPORT=usb scripts/agentlight status
AGENTLIGHT_TRANSPORT=ble-system scripts/agentlight wechat-group-new
AGENTLIGHT_TRANSPORT=http AGENTLIGHT_BASE_URL=http://192.168.4.1 scripts/agentlight wechat-friend-new
```

## 微信消息服务

示例配置在 [config/wechat-agentlight.example.json](./config/wechat-agentlight.example.json)。

前台检查：

```bash
scripts/agentlight-wechat check-config
scripts/agentlight-wechat doctor
scripts/agentlight-wechat once
```

用 fake helper 验证完整链路，不需要真实微信账号：

```bash
python3 - <<'PY'
import json
from pathlib import Path

config = json.loads(Path("config/wechat-agentlight.example.json").read_text())
config["sendToHardware"] = False
config["helperCommand"] = ["scripts/agentlight-wechat-fake-helper", "group"]
Path("/tmp/wechat-agentlight-test.json").write_text(json.dumps(config))
PY

scripts/agentlight-wechat once --config /tmp/wechat-agentlight-test.json
```

事件到灯效的默认映射：

| 微信消息类别 / 状态 | 灯效 lane | 含义 |
| --- | --- | --- |
| 无未读消息 / 已读清空 | `LANES:RED=OFF,YELLOW=OFF,GREEN=OFF` | 全部熄灭 |
| 群消息刚到达 | `LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF` | 黄灯闪烁 |
| 群消息仍未读 | `LANES:RED=OFF,YELLOW=BREATHE,GREEN=OFF` | 黄灯呼吸 |
| 好友消息刚到达 | `LANES:RED=OFF,YELLOW=OFF,GREEN=BLINK` | 绿灯闪烁 |
| 好友消息仍未读 | `LANES:RED=OFF,YELLOW=OFF,GREEN=BREATHE` | 绿灯呼吸 |
| 其他消息刚到达 | `LANES:RED=BLINK,YELLOW=OFF,GREEN=OFF` | 红灯闪烁 |
| 其他消息仍未读 | `LANES:RED=BREATHE,YELLOW=OFF,GREEN=OFF` | 红灯呼吸 |
| 多类消息同时未读 | `LANES:RED=...,YELLOW=...,GREEN=...` | 三路可同时点亮，互不覆盖 |
| 微信未运行 / 离线 | `LANES:RED=OFF,YELLOW=OFF,GREEN=OFF` | 全部熄灭 |
| 微信监听异常 / 权限异常 | `LANES:RED=STEADY,YELLOW=OFF,GREEN=OFF` | 红灯常亮，表示服务异常 |

默认闪烁持续 `10` 秒；10 秒后仍未读，会切换到对应呼吸灯效。已读或未读清空会立即关闭三路灯。呼吸状态会每 `30` 秒重发一次当前三路灯效，避免硬件被手动命令改乱后长期停在错误状态。macOS 只能读到 `unread-only` 弱信号时，无法确定具体会话，默认按“其他消息”走红灯。

## 平台能力

macOS helper 只使用系统通知中心里 60 秒内的新鲜 `com.tencent.xinwechat` 通知元数据做类别判断，避免旧通知误点亮已经没有未读的类别。分类规则是：包含 `@chatroom` 归为群消息，包含 `wxid_` 归为好友消息，其他来源归为其他消息。同一次轮询可输出群、好友、其他多条新鲜事件，服务会合成三路并发灯效。通知元数据不可用或过旧时，会降级为 `confidence=unread-only`，默认按其他消息点亮红灯。

普通日志不会输出联系人、会话名或消息摘要；日志中的 `category=group|friend|other` 表示本次事件的灯光分类，`confidence=notification-center` 表示来自新鲜通知中心记录，`confidence=unread-only` 表示已经降级为只能判断未读。

Windows 使用 helper 通过 UI Automation 观察微信窗口的可见未读状态和可见摘要；权限或 UI 结构不可用时会输出诊断。

项目默认不注入微信进程、不解密微信数据库、不读取完整聊天历史、不做自动回复。

## 构建与烧录

```bash
pio run -e esp32-c3-supermini
pio run -e esp32-c3-supermini -t upload
pio device monitor
```

烧录后可以直接验收：

```bash
scripts/agentlight status
scripts/agentlight wechat-group-new
scripts/agentlight wechat-friend-new
scripts/agentlight wechat-other-new
scripts/agentlight green
```

## 架构

```text
AgentLight/
├── src/                         ESP32-C3 固件
├── include/                     固件头文件
├── agentlight_wechat/           微信消息服务领域、应用、基础设施和 CLI
├── desktop/
│   ├── macos/                   macOS 蓝牙 helper 和微信观察 helper
│   └── windows/                 Windows 微信观察 helper
├── scripts/
│   ├── agentlight               硬件命令桥
│   ├── agentlight-wechat        微信消息服务入口
│   ├── agentlight-wechat-event  JSONL 微信事件生成工具
│   ├── agentlight-wechat-gate   单事件灯效映射工具
│   └── agentlight-wechat-fake-helper
├── config/
│   └── wechat-agentlight.example.json
├── service/                     macOS / Windows 后台服务安装脚本
├── tests/                       微信业务和硬件桥测试
└── docs/                        使用说明和设计文档
```

## 开源协议

AgentLight 使用 [MIT License](./LICENSE) 开源，SPDX 标识为 `MIT`。
