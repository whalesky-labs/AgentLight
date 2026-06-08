<p align="center">
  <img src="https://avatars.githubusercontent.com/u/277389313?s=200&v=4" width="128" height="128" alt="AgentLight">
</p>

<h1 align="center">AgentLight</h1>

<p align="center">
  基于 ESP32-C3 的 AI 任务状态交通灯固件。
</p>

<p align="center">
  USB 串口控制 · Bluetooth LE 控制 · Wi-Fi HTTP 控制 · 红黄绿灯状态映射
</p>

<p align="center">
  <a href="platformio.ini"><img src="https://img.shields.io/badge/Board-ESP32--C3%20SuperMini-000000?logo=espressif&logoColor=white" alt="ESP32-C3 SuperMini"></a>
  <a href="platformio.ini"><img src="https://img.shields.io/badge/PlatformIO-ready-F5822A?logo=platformio&logoColor=white" alt="PlatformIO"></a>
  <a href="platformio.ini"><img src="https://img.shields.io/badge/Framework-Arduino-00979D?logo=arduino&logoColor=white" alt="Arduino framework"></a>
  <a href="src/infrastructure/UsbCommandChannel.cpp"><img src="https://img.shields.io/badge/Control-USB%20Serial-4A90E2" alt="USB Serial"></a>
  <a href="src/infrastructure/BleCommandChannel.cpp"><img src="https://img.shields.io/badge/Control-Bluetooth%20LE-0082FC?logo=bluetooth&logoColor=white" alt="Bluetooth LE"></a>
  <a href="src/infrastructure/WifiCommandChannel.cpp"><img src="https://img.shields.io/badge/Control-Wi--Fi%20HTTP-34A853?logo=wifi&logoColor=white" alt="Wi-Fi HTTP"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
</p>

[简体中文](./README.md) | [English](./README.en.md)

# AgentLight

AgentLight 是一个基于 ESP32-C3 的桌面 AI 状态灯项目。它通过 USB 串口、Bluetooth LE 和 Wi-Fi HTTP 接收状态命令，把 Codex、Claude Code、Cursor、Gemini、Qwen、opencode 等 AI Agent 工作流的执行状态显示到玩具红绿灯上。

当前仓库包含两部分：

- **ESP32-C3 固件**：负责接收命令并控制红 / 黄 / 绿灯
- **无客户端桥接层**：通过 shell 脚本和 AI 工具 Hook 发送状态命令，不需要桌面 GUI App

## 硬件

- ESP32-C3 SuperMini
- 玩具红 / 黄 / 绿灯
- 220R 限流电阻

默认接线：

| ESP32-C3 引脚 | 连接 |
| --- | --- |
| GPIO4 | 220R -> 红灯正极 |
| GPIO5 | 220R -> 黄灯正极 |
| GPIO6 | 220R -> 绿灯正极 |
| GND | 三个灯共用负极 |

如果玩具灯是共阳接法，把 [platformio.ini](./platformio.ini) 里的 `AGENTLIGHT_ACTIVE_LOW=1`，并把共用正极接到 `3V3`。

## 命令

通过 USB 串口发送一行命令、向 BLE RX 特征写入同样文本，或者通过 Wi-Fi HTTP API 发送命令。

命令协议使用纯文本，一次发送一条命令：

- USB 串口：以 `\n` 或 `\r\n` 结尾
- BLE：向 RX 特征写入命令文本
- Wi-Fi：访问 HTTP API
- 命令不区分大小写，固件会统一转换为大写处理
- 成功切换状态时返回 `OK <STATE>`

| 命令 | 结果 |
| --- | --- |
| `GREEN` | 绿灯亮，红灯 / 黄灯灭 |
| `GREEN_BREATHE` | 绿灯呼吸 |
| `GREEN_BLINK` | 绿灯闪烁 |
| `YELLOW` | 黄灯常亮，红灯 / 绿灯灭 |
| `YELLOW_BREATHE` | 黄灯呼吸 |
| `YELLOW_BLINK` | 黄灯闪烁 |
| `RED` | 红灯常亮，黄灯 / 绿灯灭 |
| `RED_BLINK` | 红灯闪烁 |
| `RED_BREATHE` | 红灯呼吸 |
| `OFF` | 全部熄灭 |
| `PING` | 返回 `PONG` |
| `STATUS` | 返回当前灯光状态 |
| `HELP` | 返回支持的命令列表 |

响应示例：

```text
GREEN_BREATHE -> OK GREEN_BREATHE
YELLOW_BLINK  -> OK YELLOW_BLINK
STATUS        -> STATUS YELLOW_BLINK
PING          -> PONG
```

BLE 设备名：`WHALESKY-LABS-AGENTLIGHT`

BLE 服务与特征：

| 项目 | UUID |
| --- | --- |
| 服务 | `8f16d7a0-6c6d-4d68-8d64-6b4d2a86b601` |
| RX 写入 | `8f16d7a1-6c6d-4d68-8d64-6b4d2a86b601` |
| TX 通知 / 读取 | `8f16d7a2-6c6d-4d68-8d64-6b4d2a86b601` |

## Wi-Fi HTTP

固件默认启动一个 Wi-Fi AP：

| 配置 | 默认值 |
| --- | --- |
| SSID | `WHALESKY-LABS-AGENTLIGHT` |
| 密码 | `agentlight` |
| 网关地址 | `192.168.4.1` |

HTTP API：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/` | 查看可用接口 |
| `GET` | `/status` | 查询当前状态 |
| `GET` | `/command?cmd=GREEN` | 发送命令 |
| `POST` | `/command` | 通过 plain text body 发送命令 |

测试示例：

```bash
curl "http://192.168.4.1/status"
curl "http://192.168.4.1/command?cmd=YELLOW_BLINK"
curl -X POST "http://192.168.4.1/command" --data "GREEN_BREATHE"
```

SSID 和密码可以在 [platformio.ini](./platformio.ini) 中通过 `AGENTLIGHT_WIFI_AP_SSID` 和 `AGENTLIGHT_WIFI_AP_PASSWORD` 修改。

## 脚本桥接

第二阶段不做桌面客户端 App，而是通过 `scripts/agentlight` 直接向设备发送命令。默认使用 Wi-Fi HTTP。

```bash
scripts/agentlight status
scripts/agentlight yellow-blink
scripts/agentlight green
scripts/agentlight red-blink
```

脚本支持别名：

| 输入 | 实际命令 |
| --- | --- |
| `busy` / `running` / `tool` | `YELLOW_BLINK` |
| `thinking` / `generating` | `YELLOW_BREATHE` |
| `idle` / `ready` / `done` / `success` | `GREEN` |
| `waiting` / `confirm` / `blocked` | `RED_BLINK` |
| `error` / `failed` | `RED` |

可配置环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AGENTLIGHT_HOST` | `192.168.4.1` | 设备 HTTP 地址 |
| `AGENTLIGHT_BASE_URL` | 空 | 完整基础 URL，优先级高于 host |
| `AGENTLIGHT_TIMEOUT` | `2` | curl 超时时间，单位秒 |

## 后台 Agent 服务

电脑端推荐做成后台 Agent 服务，而不是桌面 App：

| 系统 | 形态 |
| --- | --- |
| Windows | Windows Service Agent |
| macOS | LaunchAgent |
| Linux | systemd user service |

统一服务入口是 `scripts/agentlight-agent`，安装脚本位于 `service/windows` 和 `service/macos`。完整说明见 [docs/agent-service.md](./docs/agent-service.md)。

## 事件 Gate

`scripts/agentlight-gate` 用来承接 AI 工具生命周期事件，并做简单防抖和去重。

```bash
scripts/agentlight-gate start
scripts/agentlight-gate tool
scripts/agentlight-gate thinking
scripts/agentlight-gate done
scripts/agentlight-gate waiting
scripts/agentlight-gate error
```

| 事件 | 灯效 |
| --- | --- |
| `start` | `YELLOW_BLINK` |
| `tool` | `YELLOW_BLINK` |
| `thinking` | `YELLOW_BREATHE` |
| `done` | `GREEN_BLINK` |
| `waiting` | `RED_BLINK` |
| `error` | `RED` |

## AI Hook 集成

第三阶段不做 GUI 客户端，优先通过 Hook 接入：

- 多 Agent 统一入口：见 [hooks/agents/README.md](./hooks/agents/README.md)
- Cursor：见 [hooks/cursor/README.md](./hooks/cursor/README.md)
- Codex：见 [hooks/codex/README.md](./hooks/codex/README.md)
- Claude Code：见 [hooks/claude/README.md](./hooks/claude/README.md)
- Gemini CLI：见 [hooks/gemini/README.md](./hooks/gemini/README.md)
- Qwen Code：见 [hooks/qwen/README.md](./hooks/qwen/README.md)
- opencode：见 [hooks/opencode/README.md](./hooks/opencode/README.md)
- Copilot CLI：见 [hooks/copilot/README.md](./hooks/copilot/README.md)
- Kimi：见 [hooks/kimi/README.md](./hooks/kimi/README.md)
- CodeBuddy：见 [hooks/codebuddy/README.md](./hooks/codebuddy/README.md)
- Kiro：见 [hooks/kiro/README.md](./hooks/kiro/README.md)
- Antigravity：见 [hooks/antigravity/README.md](./hooks/antigravity/README.md)
- OpenClaw：见 [hooks/openclaw/README.md](./hooks/openclaw/README.md)
- Hermes：见 [hooks/hermes/README.md](./hooks/hermes/README.md)
- Pi：见 [hooks/pi/README.md](./hooks/pi/README.md)

完整平台兼容矩阵见 [docs/agent-platform-compatibility.md](./docs/agent-platform-compatibility.md)。矩阵会区分“已实现监听器 / Hook 模板 / 通用 wrapper 接入”，避免把通用入口写成已经完成的原生集成。

所有平台最终都调用同一个归一化入口：

```bash
scripts/agentlight-event --agent <agent> --event <event> --send
```

当前统一入口支持这些 Agent 名称：

| 平台 | 支持方式 |
| --- | --- |
| Codex CLI / Desktop | session 文件监听 + 统一事件入口 + wrapper 文档 |
| Claude Code | 统一事件入口 + hook/wrapper 文档 |
| Cursor Agent | Cursor Hook 模板 |
| Gemini CLI / Qwen Code / GitHub Copilot CLI / opencode | 通用 wrapper 入口 |
| Kimi / CodeBuddy / Kiro / Antigravity / OpenClaw / Hermes / Pi | 通用事件入口 + wrapper 文档，等待具体工具 hook 接入 |
| ChatGPT Desktop / Claude Desktop | 暂无稳定公开 hook；可通过外部自动化或未来适配接入统一事件入口 |

说明：AgentLight 不做桌面宠物、托盘面板、Dashboard、权限气泡或终端聚焦；这些仍由原 AI 工具或其他桌面客户端处理。本项目只负责把可观察到的 Agent 状态同步到硬件红黄绿灯。

Codex 也支持通过本地 session 文件进行只读监听。这个方式适合先验证“Codex 工作状态能不能被观察到”，不直接控制硬件：

```bash
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --from-start
scripts/codex-session-monitor --once --limit 20
```

监听器会把 Codex session JSONL 记录归一化为：

| 输出状态 | 来源示例 |
| --- | --- |
| `prompt` | `user_message` |
| `thinking` | `task_started` / `reasoning` |
| `working` | `function_call` / `web_search_call` |
| `typing` | `agent_message` / `message` |
| `success` | `task_complete` |
| `error` | `turn_aborted` |

如果要把多个平台的日志/命令输出接入统一事件流，可以使用配置化监听器：

```bash
scripts/multi-agent-monitor --config config/agent-monitors.example.json
scripts/multi-agent-monitor --config config/agent-monitors.example.json --send
```

配置文件支持：

- `file` 类型：tail 文本日志或 JSONL 日志
- `command` 类型：运行一个命令并读取 stdout
- `rules`：用 `contains` / `equals` / `json_path` 把平台输出映射到统一事件

## 状态约定

| 状态 | 灯效 | 含义 |
| --- | --- | --- |
| `OFF` | 全灭 | 未连接 / 关闭 |
| `GREEN` | 绿灯常亮 | 空闲，可开始新任务 |
| `GREEN_BREATHE` | 绿灯呼吸 | 已连接，待命中 |
| `GREEN_BLINK` | 绿灯闪烁 | 任务完成提示 / 心跳测试 |
| `YELLOW` | 黄灯常亮 | AI 正在执行普通任务 |
| `YELLOW_BREATHE` | 黄灯呼吸 | AI 正在长时间思考 / 生成 |
| `YELLOW_BLINK` | 黄灯闪烁 | 工具调用 / 命令执行中 |
| `RED` | 红灯常亮 | 错误 |
| `RED_BLINK` | 红灯闪烁 | 需要人工确认 / 阻塞 |
| `RED_BREATHE` | 红灯呼吸 | 低优先级提醒 / 等待查看 |

## 灯效时序

| 灯效 | 固件行为 |
| --- | --- |
| 常亮 | 目标颜色持续点亮，其他颜色熄灭 |
| 闪烁 | 800ms 周期，亮 400ms / 灭 400ms |
| 呼吸 | 2000ms 周期，亮度从低到高再回落 |

当前呼吸效果使用软件 PWM 实现，不需要额外硬件。对于玩具灯或普通 LED，220R 电阻仍然需要串联在 GPIO 与 LED 之间。

## 架构

```text
AgentLight/
├── src/
│   ├── domain/                 命令、颜色、灯效与状态模式模型
│   ├── application/            状态灯业务用例，负责命令处理与当前状态维护
│   ├── infrastructure/         GPIO / USB 串口 / BLE / Wi-Fi HTTP 通道实现
│   └── main.cpp                固件装配入口，连接业务层与硬件通道
├── scripts/
│   ├── agentlight              无客户端命令桥接入口
│   ├── agentlight-gate         AI 事件到灯光状态的节流与映射
│   ├── agentlight-event        多 Agent 事件归一化入口
│   ├── agentlight-agent        后台 Agent 服务入口
│   ├── codex-session-monitor   Codex session 文件状态监听器
│   └── multi-agent-monitor     多 Agent 配置化日志/命令监听器
├── hooks/                      AI 工具 Hook 模板与接入说明
├── service/
│   ├── windows/                Windows Service Agent 安装脚本
│   └── macos/                  macOS LaunchAgent 安装脚本
├── config/
│   ├── agent-monitors.example.json      监听器示例配置
│   ├── agentlight-agent.example.json    后台 Agent 服务示例配置
│   └── agent-platforms.json             AI Agent 兼容平台清单
├── docs/                       服务与兼容性文档
├── platformio.ini              ESP32-C3 SuperMini 固件构建配置
└── CHANGELOG.md                中英双语版本发布说明
```

分层原则：

- `domain` 不直接访问硬件，只定义状态与命令协议
- `application` 不关心 USB、BLE、Wi-Fi 或 GPIO 细节，只处理业务语义
- `infrastructure` 承担硬件 IO、串口、BLE 和 Wi-Fi HTTP 适配
- `main.cpp` 只负责对象装配和主循环调度

## 构建与烧录

本项目使用 PlatformIO + Arduino framework。

```bash
pio run
pio run -t upload
pio device monitor
```

如果看不到 USB 串口，请确认：

- 已安装 PlatformIO 的 ESP32 平台
- USB 线支持数据传输，不只是充电线
- `platformio.ini` 中已开启 `ARDUINO_USB_CDC_ON_BOOT=1`

## CI 固件构建

GitHub Actions 会在 `main` 分支推送、Pull Request、`v*` 标签和手动触发时构建固件包。

固件版本号规则：

| 场景 | 版本号来源 |
| --- | --- |
| 推送 `v*` tag | 使用 tag 名称，例如 `v1.2026.051+1775834670` |
| 手动触发并填写 `version` | 使用填写的版本号 |
| 普通 push / PR | 自动生成 `v1.<Year>.<DayOfYear>+<GITHUB_RUN_NUMBER>`，末尾构建号由 CI 自动递增 |

发布版本使用 CalVer：

| 字段 | 规则 | 示例 |
| --- | --- | --- |
| 展示版本 | `<Major>.<Year>.<DayOfYear> (<BuildNumber>)` | `1.2026.051 (1775834670)` |
| Git tag | `v<Major>.<Year>.<DayOfYear>+<BuildNumber>` | `v1.2026.051+1775834670` |
| 短版本 | `<Major>.<Year>.<DayOfYear>` | `1.2026.051` |
| 构建号 | `<BuildNumber>` | `1775834670` |

构建通道：

| 通道 | 说明 |
| --- | --- |
| `stable` | 正式构建，Release 不标记为预发布；推送 `v*` tag 时默认使用 |
| `preview` | 预览构建，Release 标记为预发布；普通 push / PR / 手动触发默认使用 |

CI 会生成并发布这些独立资产，不再额外打包 zip：

- `firmware.bin`
- `bootloader.bin`
- `partitions.bin`
- `manifest.json`
- `firmware-assets.sha256`

固件使用 Arduino ESP32 内置的 `huge_app.csv` 分区方案，面向 4MB Flash 的 ESP32-C3 SuperMini，单个 App 分区大小为 3MB，用于容纳 USB、BLE、Wi-Fi 三通道一体固件。

`manifest.json` 包含版本、构建通道、Git 提交、SHA256 和烧录 offset。版本发布说明维护在 [CHANGELOG.md](./CHANGELOG.md)，CI 会分别读取中文和英文中当前版本号对应的章节；如果没有对应章节，则读取 `Unreleased` 章节，并自动追加构建通道、构建环境、Git 提交、构建时间和资产清单。推送 `v*` tag 或手动触发时勾选发布，会自动创建 GitHub Release 并把生成后的发布说明写入 Release body。

预览构建不会默认创建 GitHub Release，但 CI 会把从 `CHANGELOG.md` 读取并生成的 Release body 输出到构建日志和 GitHub Actions Summary，便于直接查看本次版本更新说明；该 Release body 只作为 CI 临时内容，不作为固件资产发布。

## 桥接层验证

多 Agent 桥接层可以用内置脚本验证：

```bash
scripts/verify-agent-bridge
```

它会检查：

- shell 脚本语法
- Codex session monitor Python 语法
- 多 Agent 名称归一化
- 生命周期事件归一化
- hooks 文档目录是否完整
- 多 Agent monitor 示例配置是否可加载
