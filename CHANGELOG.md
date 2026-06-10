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
- 支持 `v1.<Year>.<DayOfYear>+<BuildNumber>` CalVer 版本规则，并在 CI 自动模式下递增构建号。
- 在 CI 中启用 Node.js 24 Actions 运行时，并将预览构建的版本更新说明输出到 Actions Summary。
- Bluetooth LE 通道默认启用配对 / 绑定，并通过集中配置管理设备名、展示名、GATT UUID、广播外观、配对开关和配对码。
- Bluetooth LE 默认启用标准 HID 配对外壳，主广播包发布 `AGENTLIGHT` 短名称、Keyboard 外观和 HID 服务，提升电脑与手机系统蓝牙列表的可见性。

### 说明

- 默认 Wi-Fi AP：`WHALESKY-LABS-AGENTLIGHT`
- 默认 Wi-Fi 密码：`agentlight`
- 默认 BLE 名称：`WHALESKY-LABS-AGENTLIGHT`
- 默认系统蓝牙展示名：`AGENTLIGHT`
- 默认 BLE 配对码：`521000`
