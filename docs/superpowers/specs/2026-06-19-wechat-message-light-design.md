# 微信消息指示灯设计

## 目标

本分支将 AgentLight 从 AI Agent 状态灯改为个人微信桌面消息指示灯。

系统支持 macOS 和 Windows 上的个人微信桌面客户端。电脑端服务在本机监听微信收到消息的可观察信号，将这些信号归一化为微信消息事件，应用用户本地规则，再通过现有 ESP32-C3 红 / 黄 / 绿灯硬件通道显示提醒状态。

## 不做什么

- 不注入微信进程。
- 不破解或解密微信本地聊天数据库。
- 不读取完整聊天历史。
- 不做微信机器人自动回复。
- 不绕过微信安全机制。
- 不改 ESP32-C3 固件命令协议，除非后续出现明确的硬件层需求。
- 不在默认日志中保存消息正文、发送人或会话名。

## 现有边界

现有硬件和下发链路已经足够通用：

- ESP32-C3 固件接收 `GREEN`、`YELLOW_BLINK`、`RED_BLINK`、`OFF`、`STATUS` 等纯灯光命令。
- `scripts/agentlight` 负责通过 USB Serial、系统蓝牙或 Wi-Fi HTTP 发送命令。
- 现有 AI 逻辑负责观察上游事件、归一化事件、做去重和优先级处理，然后把灯效命令交给 `scripts/agentlight`。

微信分支应保留硬件侧和 `scripts/agentlight`，替换上游事件源和业务事件语义。

## 总体架构

```text
macOS 微信监听 helper
Windows 微信监听 helper
        |
        v
微信事件归一化器
        |
        v
微信规则引擎
        |
        v
微信灯效状态机
        |
        v
scripts/agentlight
        |
        v
USB / BLE / HTTP
        |
        v
ESP32-C3 红黄绿灯
```

平台监听 helper 只负责观察本机微信信号，不决定最终灯效。归一化器产出统一事件模型。规则引擎判断消息优先级。灯效状态机负责状态转移、重复抑制、超时回绿和最终硬件命令选择。

## 平台采集策略

### macOS

macOS 没有稳定的官方 API 用来读取其他 App 的全部系统通知。Apple UserNotifications 主要用于应用管理自己的本地或远程通知。因此 macOS 端不把“直接监听微信通知中心记录”作为核心依赖。

主路径：

- 使用 Swift helper 调用 macOS Accessibility API。
- 观察微信进程是否运行。
- 观察微信 Dock 角标、窗口标题、会话列表可访问元素、未读标识和可见摘要。
- 在可访问信息足够时识别普通未读、重要联系人、重要群、关键词和疑似 @我。

辅助信号：

- 检查微信通知设置是否可能导致消息不可见。
- 必要时读取当前可见的通知横幅或微信窗口可访问文本，但不把它当作唯一信号源。

权限和诊断：

- 首次运行必须检查 Accessibility 权限。
- 权限缺失时输出明确诊断，不静默失败。
- 如果微信版本或 UI 结构导致联系人、群名、摘要不可见，监听器仍应降级产出普通 `wechat-message`，并标记能力降级。

### Windows

Windows 端有官方通知监听能力，可以作为主路径。

主路径：

- 使用 C#/.NET 或 Windows App SDK helper。
- 声明 `userNotificationListener` 能力。
- 首次运行请求用户授权通知访问。
- 通过 `UserNotificationListener` 读取微信 Toast 通知。

兜底路径：

- 使用 Windows UI Automation 观察微信进程、窗口、未读角标、会话列表和可访问文本。
- 当通知权限未开启、通知记录为空或用户关闭微信通知时，使用 UI Automation 尽量识别未读状态。

权限和诊断：

- Windows 通知监听必须检查授权状态，因为用户可以随时撤销权限。
- 如果通知监听需要应用包身份或 manifest 能力，应构建一个明确的 Windows helper，不假装普通脚本可以稳定访问。
- UI Automation 只作为可配置兜底，因为微信 UI 结构可能随版本变化。

## Helper 接口

两个平台 helper 对上层暴露相同接口：向 stdout 输出 JSONL 事件。上层 Python 服务只消费统一事件，不关心平台实现细节。

事件示例：

```json
{"source":"wechat","event":"wechat-message","platform":"macos","conversation":"","sender":"","summary":"","observedAt":"2026-06-19T12:00:00+08:00","capabilities":["unread-badge"]}
```

helper 约定：

- 一行一个 JSON 对象。
- 正常消息输出 `event`。
- 能力降级输出 `diagnostic` 字段。
- 错误输出 `wechat-listener-error`，并带上可展示的原因。
- 不负责调用硬件。
- 默认不落盘保存敏感字段。

## 统一事件模型

微信事件不复用 AI 生命周期事件，例如 `prompt`、`tool`、`done`。

| 事件 | 含义 |
| --- | --- |
| `wechat-message` | 观察到普通微信新消息或未读状态。 |
| `wechat-important` | 消息命中重要联系人、重要群、关键词或可见 @我 规则。 |
| `wechat-muted` | 消息命中免打扰或忽略规则，不改变灯效。 |
| `wechat-cleared` | 未读或提醒状态已清除，或超时策略触发回绿。 |
| `wechat-offline` | 微信未运行或当前不可观察。 |
| `wechat-listener-error` | 监听器异常，需要用户处理。 |

内部事件对象：

```json
{
  "source": "wechat",
  "event": "wechat-message",
  "platform": "macos",
  "conversation": "",
  "sender": "",
  "summary": "",
  "matchedRule": "",
  "confidence": "unread-only",
  "timestamp": "2026-06-19T12:00:00+08:00"
}
```

`conversation`、`sender`、`summary` 是敏感可选字段。默认只在内存中用于即时规则匹配，不持久化。

## 规则引擎

规则引擎把归一化微信事件分类为灯效优先级。

规则类型：

- 重要联系人。
- 重要群。
- 关键词。
- 可见 @我 标记。
- 免打扰会话。
- 全局静默时段。
- 仅能确认未读、但无法读取摘要的未知消息。

优先级：

1. 监听器错误。
2. 重要消息。
3. 普通未读消息。
4. 免打扰消息。
5. 清除状态。
6. 离线状态。

重要消息不能被后续普通消息降级。免打扰消息不改变当前灯效。

## 灯效状态机

灯效状态机拥有提醒状态和硬件命令选择权。

| 状态 | 触发 | 灯效 |
| --- | --- | --- |
| `idle` | 没有活跃未读提醒 | `GREEN` |
| `unread` | `wechat-message` | `YELLOW_BLINK` |
| `important` | `wechat-important` | `RED_BLINK` |
| `offline` | `wechat-offline` | `OFF` |
| `error` | `wechat-listener-error` | `RED` |

状态转移：

- `idle` -> `unread`：收到 `wechat-message`。
- `idle` -> `important`：收到 `wechat-important`。
- `unread` -> `important`：收到 `wechat-important`。
- `important` 收到后续普通消息时保持 `important`。
- `unread` 或 `important` -> `idle`：收到 `wechat-cleared` 或提醒超时。
- 任意状态 -> `error`：收到 `wechat-listener-error`。
- 任意非错误状态 -> `offline`：收到 `wechat-offline`。
- `error` 只在监听器恢复健康观察后退出。

默认映射：

| 事件 | 命令 |
| --- | --- |
| `wechat-message` | `YELLOW_BLINK` |
| `wechat-important` | `RED_BLINK` |
| `wechat-muted` | 不下发命令 |
| `wechat-cleared` | `GREEN` |
| `wechat-offline` | `OFF` |
| `wechat-listener-error` | `RED` |

## 清除策略

系统必须有确定的回绿策略。

支持模式：

- `timeout`：超过配置秒数后回到 `GREEN`。
- `unread-cleared`：监听器能观察到微信未读状态消失时回到 `GREEN`。
- `timeout-or-unread-cleared`：两者谁先发生就回到 `GREEN`。

默认配置：

```json
{
  "mode": "timeout-or-unread-cleared",
  "timeoutSeconds": 300
}
```

如果当前平台或权限状态无法可靠观察未读清除，监听器应报告能力降级，灯效状态机只依赖超时回绿。

## 配置

新增微信专用示例配置，和现有 AI agent 配置分开：

```json
{
  "source": "wechat",
  "platform": "auto",
  "sendToHardware": true,
  "collection": {
    "macosAccessibility": true,
    "windowsNotificationListener": true,
    "windowsUiAutomationFallback": true
  },
  "clearPolicy": {
    "mode": "timeout-or-unread-cleared",
    "timeoutSeconds": 300
  },
  "rules": {
    "importantContacts": [],
    "importantGroups": [],
    "keywords": [],
    "mutedConversations": [],
    "quietHours": []
  },
  "privacy": {
    "storeMessageContent": false,
    "logMatchedSummary": false
  },
  "hardware": {
    "AGENTLIGHT_TRANSPORT": "auto",
    "AGENTLIGHT_SERIAL_PORT": "",
    "AGENTLIGHT_SERIAL_BAUD": "115200",
    "AGENTLIGHT_HOST": "192.168.4.1",
    "AGENTLIGHT_TIMEOUT": "2"
  }
}
```

## 服务形态

### macOS

- 使用 LaunchAgent 后台运行。
- Python 主进程启动 Swift Accessibility helper。
- 首次运行检查微信进程、Accessibility 权限、硬件下发路径。
- 日志沿用现有 AgentLight macOS 日志目录风格。

### Windows

- 使用用户级后台 agent 或轻量托盘程序。
- Python 主进程启动 Windows helper。
- Windows helper 负责通知权限请求、通知读取和 UI Automation 兜底。
- 日志沿用现有 AgentLight Windows 用户日志目录风格。

## 代码组织

建议组织：

```text
agentlight_agent/
  domain/
    wechat_events.py
    wechat_rules.py
    wechat_light_state.py
  application/
    wechat_service.py
    wechat_light_gate.py
  infrastructure/
    wechat_helper_runner.py
    wechat_jsonl_parser.py
  interfaces/
    wechat_cli.py

desktop/
  macos/
    AgentLightWeChatObserver.swift
  windows/
    AgentLightWeChatObserver/

scripts/
  agentlight-wechat
  agentlight-wechat-event
  agentlight-wechat-gate

config/
  wechat-agentlight.example.json
```

`scripts/agentlight` 继续作为唯一硬件出口。微信入口围绕 `wechat` 命名，不再暴露 AI agent 语义。

## 隐私和日志

默认行为：

- 不持久化消息正文、发送人、会话名。
- 普通日志不打印消息摘要。
- 只记录事件类型、平台、命中规则名、状态转移和硬件命令。
- 诊断模式可以临时显示更多信息，但必须显式开启，默认关闭。

日志示例：

```text
event=wechat-message platform=macos confidence=unread-only state=unread command=YELLOW_BLINK
event=wechat-important platform=windows matchedRule=importantContacts state=important command=RED_BLINK
event=wechat-cleared platform=macos state=idle command=GREEN
```

## 诊断能力

CLI 应提供：

```bash
scripts/agentlight-wechat check-config
scripts/agentlight-wechat doctor
scripts/agentlight-wechat run
scripts/agentlight-wechat once
```

`doctor` 至少检查：

- 当前操作系统。
- 微信进程是否运行。
- macOS Accessibility 权限。
- Windows 通知监听授权。
- Windows UI Automation 可用性。
- helper 是否能启动并输出 JSONL。
- 硬件命令通道是否可用。
- 最近一次观察事件。
- 当前灯效状态机状态。

## 验收标准

- macOS 微信收到普通桌面消息时，灯变为黄灯闪烁。
- Windows 微信收到普通桌面消息时，灯变为黄灯闪烁。
- 命中重要联系人、重要群、关键词或可见 @我 时，灯变为红灯闪烁。
- 重要提醒不会被后续普通消息降级。
- 免打扰会话不改变当前灯效。
- 根据配置的清除策略回到绿灯。
- 微信退出或不可观察时进入 `OFF`。
- 监听器异常时红灯常亮，并输出明确诊断。
- USB、BLE、HTTP 三种硬件通道继续通过 `scripts/agentlight` 工作。
- 普通日志不保存完整消息正文、发送人或会话名。
- 关闭系统通知、撤销 Accessibility 权限或撤销 Windows 通知权限时，系统给出明确诊断。

## 官方依据

- Apple UserNotifications: <https://developer.apple.com/documentation/usernotifications>
- Apple Accessibility AXUIElement: <https://developer.apple.com/documentation/applicationservices/axuielement>
- Apple AXUIElement.h: <https://developer.apple.com/documentation/applicationservices/axuielement_h>
- Microsoft Notification Listener: <https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/notification-listener>
- Microsoft UI Automation Overview: <https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview>
