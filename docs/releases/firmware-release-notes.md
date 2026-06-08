# AgentLight 固件发布说明

## 版本信息

- 版本号：`{{VERSION}}`
- 构建环境：`{{ENVIRONMENT}}`
- Git 提交：`{{GIT_SHA}}`
- 构建时间：`{{BUILD_TIME}}`
- 固件包：`{{ARTIFACT_NAME}}`
- 校验文件：`firmware-package.sha256`

## 本次发布

- 构建 ESP32-C3 SuperMini 固件。
- 固件支持 USB Serial、Bluetooth LE、Wi-Fi HTTP 三种控制通道。
- 固件支持红 / 黄 / 绿常亮、闪烁、呼吸状态命令。
- 桥接层支持多 AI Agent 状态事件归一化。

## 烧录提示

1. 下载本次 Release 中的固件包。
2. 解压后确认包含 `firmware.bin`、`bootloader.bin`、`partitions.bin` 和 `manifest.json`。
3. 使用 PlatformIO、esptool 或后续提供的烧录脚本写入 ESP32-C3 SuperMini。

## 注意事项

- 默认 Wi-Fi AP：`WHALESKY-LABS-AGENTLIGHT`
- 默认 Wi-Fi 密码：`agentlight`
- 默认 BLE 名称：`WHALESKY-LABS-AGENTLIGHT`
- 如需修改 GPIO、Wi-Fi 名称或密码，请调整 `platformio.ini` 后重新构建。
