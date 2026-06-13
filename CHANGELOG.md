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
- Bluetooth LE 默认使用系统蓝牙可见的 HID Presentation Remote 外观，用户通过电脑系统蓝牙连接或断开设备，灯光控制仍走 AgentLight 自定义 GATT 服务。
- 固件根据 USB 主机连接状态在 USB 模式和蓝牙模式之间切换；USB 模式会挂起 BLE 广播、断开已连接 BLE 客户端并拒收 BLE 命令。
- 桥接脚本默认使用 `auto` 通道：检测到 USB 串口时走 USB，没有 USB 串口时走系统蓝牙。
- CI Release 资产补充 `boot_app0.bin`，发布说明同步写入四段烧录 offset，便于按 `manifest.json` 完整烧录 ESP32-C3 SuperMini。

### 说明

- 默认 Wi-Fi AP：`WHALESKY-LABS-AGENTLIGHT`
- 默认 Wi-Fi 密码：`12345678`
- 默认 BLE 名称：`WHALESKY-LABS-AGENTLIGHT`
- 默认系统蓝牙展示名：`AGENTLIGHT`
- 默认 BLE 配对码：`123456`
