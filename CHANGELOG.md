# CHANGELOG

本文件记录 AgentLight 的版本发布说明。CI 构建 GitHub Release 时会读取本文件内容，并优先使用当前版本号对应的章节；如果没有找到对应章节，则使用 `Unreleased` 章节内容生成本次版本的发布说明。

## Unreleased

### 新增

- 支持 ESP32-C3 SuperMini 固件构建。
- 支持 USB Serial、Bluetooth LE、Wi-Fi HTTP 三种控制通道。
- 支持红 / 黄 / 绿常亮、闪烁、呼吸状态命令。
- 支持多 AI Agent 状态事件归一化与后台 Agent 服务。
- 支持 CI 正式构建和预览构建，并将固件资产直接发布到 GitHub Releases。
- 使用 4MB Flash 单 App 分区表，避免 USB、BLE、Wi-Fi 三通道固件超过默认 App 分区。

### 说明

- 默认 Wi-Fi AP：`WHALESKY-LABS-AGENTLIGHT`
- 默认 Wi-Fi 密码：`agentlight`
- 默认 BLE 名称：`WHALESKY-LABS-AGENTLIGHT`
