# AgentLight

AgentLight is an ESP32-C3 desktop WeChat message indicator. A local macOS or Windows service observes personal desktop WeChat signals, normalizes them into WeChat events, applies local rules, and drives a red/yellow/green traffic light through USB serial, system Bluetooth, or Wi-Fi HTTP.

This branch is WeChat-only. It keeps the firmware and hardware command bridge, and does not ship the previous upstream tool integrations.

## Hardware

- ESP32-C3 SuperMini
- BS-768 red/yellow/green traffic light board
- One 220R resistor per LED control line

See [docs/user-guide.md](./docs/user-guide.md) for wiring, flashing, service setup, and troubleshooting.

## Hardware Commands

```bash
scripts/agentlight status
scripts/agentlight green
scripts/agentlight yellow-blink
scripts/agentlight red-blink
```

Default transport is `auto`: USB when a serial device is present, otherwise system Bluetooth. HTTP is also supported:

```bash
AGENTLIGHT_TRANSPORT=http AGENTLIGHT_BASE_URL=http://192.168.4.1 scripts/agentlight yellow-blink
```

## WeChat Service

```bash
scripts/agentlight-wechat check-config
scripts/agentlight-wechat doctor
scripts/agentlight-wechat once
```

Example config: [config/wechat-agentlight.example.json](./config/wechat-agentlight.example.json).

Default event mapping:

| Event | Light |
| --- | --- |
| `wechat-message` | `YELLOW_BLINK` |
| `wechat-important` | `RED_BLINK` |
| `wechat-muted` | unchanged |
| `wechat-cleared` | `OFF` |
| `wechat-offline` | `OFF` |
| `wechat-listener-error` | `RED` |

The macOS helper uses Accessibility observations. The Windows helper uses UI Automation observations of visible WeChat window state. AgentLight does not inject into WeChat, decrypt WeChat databases, read full chat history, or automate replies.

## Firmware

```bash
pio run -e esp32-c3-supermini
pio run -e esp32-c3-supermini -t upload
pio device monitor
```

## License

AgentLight is released under the [MIT License](./LICENSE).
