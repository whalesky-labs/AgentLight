# CHANGELOG

本文件记录 AgentLight 的版本发布说明。内容按版本累积维护，最新未发布内容始终写在 `Unreleased` 章节。

CI 构建 GitHub Release 时只读取一个章节：优先读取当前版本号对应的章节；如果没有找到对应章节，则读取 `Unreleased` 章节。历史版本章节会保留在本文件中，但不会进入本次 Release body。

## Unreleased

### 新增

- 固件上电后执行启动自检：红灯、黄灯、绿灯依次点亮，再三灯同时闪烁 3 次。
- 固件根据 USB 主机连接状态在 USB 模式和蓝牙模式之间自动切换；USB 模式会挂起 BLE 广播、断开已连接 BLE 客户端并拒收 BLE 命令。
- 电脑端后台服务默认使用 `auto` 通道：检测到 USB 串口时走 USB，没有 USB 串口时走系统蓝牙。
- macOS 系统蓝牙桥接支持自动构建和后台服务安装流程，服务启动后即可按当前活动平台同步 AI 状态。
- CI Release 资产补充 `boot_app0.bin`，发布说明同步写入四段烧录 offset，便于按 `manifest.json` 完整烧录 ESP32-C3 SuperMini。

### 修复

- 修复切换 USB 口后串口路径变化导致后台服务仍指向旧设备的问题，USB 通道保持自动检测。
- 修正 BS-768 灯板接线文档：当前灯板仅保留灯珠，每一路 GPIO 到灯珠控制脚都需要单独串联 220R。
- 修复非 macOS CI Runner 中 `auto` 通道无法通过显式 BLE helper 验证的问题；真实环境未提供 BLE helper 时仍保持非 macOS 不支持系统蓝牙的错误边界。

## v1.2026.164+42

### 新增

- 支持 ESP32-C3 SuperMini 固件构建。
- 支持 USB Serial、Bluetooth LE、Wi-Fi HTTP 三种控制通道。
- 支持红 / 黄 / 绿常亮、闪烁、呼吸状态命令。
- 支持 `ALL`、`ALL_BLINK`、`ALL_BREATHE` 三灯自检命令。
- 支持多 AI Agent 状态事件归一化与后台 Agent 服务。
- 支持 CI 正式构建和预览构建，并将固件资产直接发布到 GitHub Releases。
- 使用 4MB Flash 单 App 分区表，避免 USB、BLE、Wi-Fi 三通道固件超过默认 App 分区。
- 支持 `v1.<Year>.<DayOfYear>+<BuildNumber>` CalVer 版本规则，并在 CI 自动模式下递增构建号。
- 在 CI 中启用 Node.js 24 Actions 运行时，并将预览构建的版本更新说明输出到 Actions Summary。
- Bluetooth LE 通道默认启用配对 / 绑定，并通过集中配置管理设备名、展示名、GATT UUID、广播外观、配对开关和配对码。
- Bluetooth LE 默认使用系统蓝牙可见的 HID Presentation Remote 外观，用户通过电脑系统蓝牙连接或断开设备，灯光控制仍走 AgentLight 自定义 GATT 服务。

### 变更

- `YELLOW_BLINK` 使用 400ms 周期，作为工具执行中的快速反馈；其他闪烁状态保持 800ms 周期。
- 项目文档改为中文优先，除 `README.en.md` 外，公开 Markdown 文档正文保持中文。
- 开源协议采用 MIT License，并为源码、脚本和服务安装文件补充统一文件头。

### 说明

- 默认 Wi-Fi AP：`WHALESKY-LABS-AGENTLIGHT`
- 默认 Wi-Fi 密码：`12345678`
- 默认 BLE 名称：`WHALESKY-LABS-AGENTLIGHT`
- 默认系统蓝牙展示名：`AGENTLIGHT`
- 默认 BLE 配对码：`123456`
