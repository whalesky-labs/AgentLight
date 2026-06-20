# AgentLight

AgentLight is an ESP32-C3 desktop WeChat message indicator. A local macOS or Windows service observes personal desktop WeChat signals, classifies messages as group, friend, or other, and drives independent red/yellow/green light lanes through USB serial, system Bluetooth, or Wi-Fi HTTP.

This branch is WeChat-only. It keeps the firmware and hardware command bridge, and does not ship the previous upstream tool integrations.

## Hardware

- ESP32-C3 SuperMini
- BS-768 red/yellow/green traffic light board
- One 220R resistor per LED control line

See [docs/user-guide.md](./docs/user-guide.md) for wiring, flashing, service setup, and troubleshooting.

## Hardware Commands

```bash
scripts/agentlight status
scripts/agentlight wechat-group-new
scripts/agentlight wechat-friend-new
scripts/agentlight wechat-other-new
```

Default transport is `auto`: USB when a serial device is present, otherwise system Bluetooth. HTTP is also supported:

```bash
AGENTLIGHT_TRANSPORT=http AGENTLIGHT_BASE_URL=http://192.168.4.1 scripts/agentlight wechat-group-new
```

## WeChat Service

```bash
scripts/agentlight-wechat check-config
scripts/agentlight-wechat doctor
scripts/agentlight-wechat once
```

Example config: [config/wechat-agentlight.example.json](./config/wechat-agentlight.example.json).

Default light mapping:

| WeChat message category / state | Light lanes | Meaning |
| --- | --- | --- |
| No unread messages / unread cleared | `LANES:RED=OFF,YELLOW=OFF,GREEN=OFF` | All lights off |
| New group message | `LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF` | Yellow blink |
| Group message still unread | `LANES:RED=OFF,YELLOW=BREATHE,GREEN=OFF` | Yellow breathe |
| New friend message | `LANES:RED=OFF,YELLOW=OFF,GREEN=BLINK` | Green blink |
| Friend message still unread | `LANES:RED=OFF,YELLOW=OFF,GREEN=BREATHE` | Green breathe |
| New other message | `LANES:RED=BLINK,YELLOW=OFF,GREEN=OFF` | Red blink |
| Other message still unread | `LANES:RED=BREATHE,YELLOW=OFF,GREEN=OFF` | Red breathe |
| Multiple unread categories | `LANES:RED=...,YELLOW=...,GREEN=...` | Independent lanes can stay active together |
| WeChat offline | `LANES:RED=OFF,YELLOW=OFF,GREEN=OFF` | All lights off |
| Listener or permission error | `LANES:RED=STEADY,YELLOW=OFF,GREEN=OFF` | Solid red means service error |

Blinking lasts `10` seconds by default. If the message is still unread after that, the lane switches to breathe. Clearing unread messages turns all lanes off immediately. While breathing, AgentLight refreshes the current lane command every `30` seconds. When macOS only exposes an `unread-only` signal, AgentLight treats it as an other message and uses the red lane.

The macOS helper reads fresh `com.tencent.xinwechat` Notification Center metadata when available. If the WeChat UI still shows unread messages after macOS has archived the fresh notification, the helper recovers unread categories from the recent 6-hour notification history. `@chatroom` is classified as group, `wxid_` as friend, and everything else as other. One helper poll can emit group, friend, and other events together, and the service merges them into concurrent light lanes. The Windows helper uses UI Automation observations of visible WeChat window state. AgentLight does not inject into WeChat, decrypt WeChat databases, read full chat history, or automate replies.

## Firmware

```bash
pio run -e esp32-c3-supermini
pio run -e esp32-c3-supermini -t upload
pio device monitor
```

## License

AgentLight is released under the [MIT License](./LICENSE).
