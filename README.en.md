<p align="center">
  <img src="https://avatars.githubusercontent.com/u/277389313?s=200&v=4" width="128" height="128" alt="AgentLight">
</p>

<h1 align="center">牛马工作指示灯 · AgentLight</h1>

<p align="center">
  ESP32-C3 traffic light firmware for AI task status.
</p>

<p align="center">
  USB Serial Control · Bluetooth LE Control · Wi-Fi HTTP Control · Red Yellow Green Mapping
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

AgentLight is an ESP32-C3 desktop AI status light project. It supports USB
serial, Bluetooth LE, and Wi-Fi HTTP commands so Codex, Claude Code, Cursor,
Gemini, Qwen, opencode, and other AI agent workflows can show task state on a
toy traffic light.

This repository contains two parts:

- **ESP32-C3 firmware**: receives commands and controls the red/yellow/green lights
- **Desktop agent service**: monitors AI tool state and forwards state commands to the configured hardware channel

The complete user guide is available in Chinese at [docs/user-guide.md](./docs/user-guide.md).

## Hardware

- ESP32-C3 SuperMini
- BS-768 toy red/yellow/green traffic light board
- one 220R resistor on each light control line

For the wiring diagram, pin table, and soldering reference photos, see the
[Chinese user guide](./docs/user-guide.md).

## Commands

Send one command per line over USB serial, write the command to the HID vendor
feature report of the already connected system Bluetooth device, or send
commands through the Wi-Fi HTTP API. Generic BLE test clients can also write to
the custom RX characteristic directly.

The protocol is plain text, one command at a time:

- USB serial: terminate each command with `\n` or `\r\n`
- System Bluetooth: write the command text to the HID vendor feature report
- BLE GATT: write the command text to the RX characteristic
- Wi-Fi: call the HTTP API
- Commands are case-insensitive and normalized to uppercase by the firmware
- Successful state changes return `OK <STATE>`

| Command | Result |
| --- | --- |
| `GREEN` | Green on, red/yellow off |
| `GREEN_BREATHE` | Green breathing |
| `GREEN_BLINK` | Green blinking |
| `YELLOW` | Yellow steady, red/green off |
| `YELLOW_BREATHE` | Yellow breathing |
| `YELLOW_BLINK` | Yellow blinking |
| `RED` | Red steady, yellow/green off |
| `RED_BLINK` | Red blinking |
| `RED_BREATHE` | Red breathing |
| `ALL` | Red/yellow/green steady on for hardware self-test |
| `ALL_BLINK` | Red/yellow/green blinking together |
| `ALL_BREATHE` | Red/yellow/green breathing together |
| `OFF` | All lights off |
| `PING` | Responds `PONG` |
| `STATUS` | Responds with the current light state |
| `HELP` | Responds with supported commands |

Response examples:

```text
GREEN_BREATHE -> OK GREEN_BREATHE
YELLOW_BLINK  -> OK YELLOW_BLINK
STATUS        -> STATUS YELLOW_BLINK
PING          -> PONG
```

On power-up, the firmware runs a startup self-test: red, yellow, and green turn on in sequence, then all three lights blink together 3 times to indicate initialization is complete.

BLE device name: `WHALESKY-LABS-AGENTLIGHT`

BLE advertised short name: `AGENTLIGHT`

BLE pairing / bonding is enabled by default. Pairing PIN:

```text
123456
```

This is an ESP32-C3 BLE connection, not Bluetooth Classic SPP, keyboard, mouse, or audio. Users connect or disconnect AgentLight from the operating system Bluetooth settings. The background service does not expose a local web page for Bluetooth connection management, and it does not reconnect the device after the user disconnects it. The firmware advertises a standard HID Presentation Remote appearance so the operating system Bluetooth list can show it reliably, and system Bluetooth commands are sent through a HID vendor feature report. Generic BLE test clients can still use the AgentLight custom RX / TX GATT service. The firmware does not send keyboard or mouse input events. The first encrypted TX read, notification subscription, RX write, or HID command report write triggers pairing; after pairing succeeds, commands such as `PING`, `STATUS`, and `YELLOW_BLINK` can be sent. When a USB host is connected, the firmware enters USB mode, suspends BLE advertising, disconnects any BLE client, and rejects BLE commands so operating-system Bluetooth reconnection cannot affect the lights. Without a USB host, the firmware enters Bluetooth mode. When BLE disconnects, the firmware switches to `OFF` and closes connectable advertising to avoid operating-system auto-reconnection. To reconnect, hold the ESP32-C3 onboard `BOOT` button for 2 seconds to open a 60-second manual connection window, then connect from system Bluetooth settings.

BLE service and characteristics:

| Item | UUID |
| --- | --- |
| Service | `8f16d7a0-6c6d-4d68-8d64-6b4d2a86b601` |
| RX write | `8f16d7a1-6c6d-4d68-8d64-6b4d2a86b601` |
| TX notify/read | `8f16d7a2-6c6d-4d68-8d64-6b4d2a86b601` |

## Wi-Fi HTTP

The firmware starts a Wi-Fi AP by default:

| Setting | Default |
| --- | --- |
| SSID | `WHALESKY-LABS-AGENTLIGHT` |
| Password | `12345678` |
| Gateway | `192.168.4.1` |

HTTP API:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Show available endpoints |
| `GET` | `/status` | Read the current state |
| `GET` | `/command?cmd=GREEN` | Send a command |
| `POST` | `/command` | Send a plain text command body |

Examples:

```bash
curl "http://192.168.4.1/status"
curl "http://192.168.4.1/command?cmd=YELLOW_BLINK"
curl -X POST "http://192.168.4.1/command" --data "GREEN_BREATHE"
```

The SSID and password can be changed in [platformio.ini](./platformio.ini) via
`AGENTLIGHT_WIFI_AP_SSID` and `AGENTLIGHT_WIFI_AP_PASSWORD`.

## Script Bridge

Stage 2 does not require a desktop GUI app. Use `scripts/agentlight` to send
commands directly to the device. The default transport is automatic: USB serial
is used when a USB port is present; otherwise the bridge uses system Bluetooth.
The firmware also switches between USB mode and Bluetooth mode from the USB host
connection state.

```bash
scripts/agentlight status
scripts/agentlight yellow-blink
scripts/agentlight green
scripts/agentlight red-blink
```

Use USB serial control:

```bash
AGENTLIGHT_TRANSPORT=usb scripts/agentlight status
AGENTLIGHT_TRANSPORT=usb scripts/agentlight yellow-blink
```

Use system Bluetooth control after connecting `AGENTLIGHT` in the operating
system Bluetooth settings:

```bash
AGENTLIGHT_TRANSPORT=ble-system scripts/agentlight status
AGENTLIGHT_TRANSPORT=ble-system scripts/agentlight yellow-blink
```

`ble-system` only uses an already connected system BLE device and sends commands
through a HID vendor feature report. If the user has not connected AgentLight in
Bluetooth settings, the bridge returns `SKIP BLE_NOT_CONNECTED` and does not
scan, connect, or reconnect automatically. When BLE disconnects, the firmware
enters `OFF` and closes connectable advertising. To reconnect, hold the
ESP32-C3 onboard `BOOT` button for 2 seconds to open a 60-second manual
connection window.

By default, the bridge auto-detects common USB serial ports such as `/dev/cu.usbmodem*`. If multiple devices are connected, set `AGENTLIGHT_SERIAL_PORT` to select one explicitly.

Supported aliases:

| Input | Command |
| --- | --- |
| `busy` / `running` / `tool` | `YELLOW_BLINK` |
| `thinking` / `generating` | `YELLOW_BREATHE` |
| `idle` / `ready` / `done` / `success` | `GREEN` |
| `waiting` / `confirm` / `blocked` | `RED_BLINK` |
| `error` / `failed` | `RED` |

Environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `AGENTLIGHT_TRANSPORT` | `auto` | Control channel, supports `auto` / `usb` / `ble-system` / `http`; `auto` uses USB when present and system Bluetooth when USB is absent |
| `AGENTLIGHT_SERIAL_PORT` | empty | USB serial port; when empty, common USB serial ports are auto-detected |
| `AGENTLIGHT_SERIAL_BAUD` | `115200` | USB serial baud rate |
| `AGENTLIGHT_BLE_DEVICE_NAME` | `WHALESKY-LABS-AGENTLIGHT` | Already connected system Bluetooth device name |
| `AGENTLIGHT_HOST` | `192.168.4.1` | Device HTTP host |
| `AGENTLIGHT_BASE_URL` | empty | Full base URL, higher priority than host |
| `AGENTLIGHT_TIMEOUT` | `2` | curl timeout in seconds |

## Background Agent Service

The computer-side bridge should run as a background agent service rather than a
desktop app:

| System | Form |
| --- | --- |
| Windows | Windows Service Agent |
| macOS | LaunchAgent |
| Linux | systemd user service |

The shared service entrypoint is `scripts/agentlight-agent`, with install
scripts under `service/windows` and `service/macos`. See
[docs/user-guide.md](./docs/user-guide.md).

Users connect or disconnect Bluetooth only from the operating system Bluetooth
settings. The background service listens for AI status and sends light commands;
it does not own Bluetooth connection management.

## Event Gate

`scripts/agentlight-gate` receives AI lifecycle events, maps them to light
states, and suppresses exact duplicate events within a short time window so the
same state is not sent repeatedly.

```bash
scripts/agentlight-gate start
scripts/agentlight-gate tool
scripts/agentlight-gate thinking
scripts/agentlight-gate done
scripts/agentlight-gate waiting
scripts/agentlight-gate error
```

| Event | Light state |
| --- | --- |
| `start` | `YELLOW_BLINK` |
| `tool` | `YELLOW_BLINK` |
| `thinking` | `YELLOW_BREATHE` |
| `done` | `GREEN_BLINK` -> `GREEN` |
| `waiting` | `RED_BLINK` |
| `error` | `RED` |

## AI Hook Integration

Stage 3 uses hooks instead of a GUI client:

- Multi-agent entrypoint: see [hooks/agents/README.md](./hooks/agents/README.md)
- Codex: see [hooks/codex/README.md](./hooks/codex/README.md)
- Cursor: see [hooks/cursor/README.md](./hooks/cursor/README.md)

Claude Code, Gemini CLI, Qwen Code, opencode, Copilot CLI, Kimi, CodeBuddy,
Kiro, Antigravity, OpenClaw, Hermes, Pi, and similar platforms use the shared
multi-agent entrypoint or generic wrapper. The project does not maintain one
duplicated template document per generic platform.

The platform list and support mode are defined in
[config/agent-platforms.json](./config/agent-platforms.json), with integration
instructions kept in [hooks/agents/README.md](./hooks/agents/README.md).

All platforms eventually call the same normalized entrypoint:

```bash
scripts/agentlight-event --agent <agent> --event <event> --send
```

The shared entrypoint currently supports these agent names:

| Platform | Support mode |
| --- | --- |
| Codex CLI / Desktop | session file monitor plus shared event entrypoint and wrapper docs |
| Claude Code | shared event entrypoint plus hook/wrapper docs |
| Cursor Agent | Cursor hook template |
| Gemini CLI / Qwen Code / GitHub Copilot CLI / opencode | generic wrapper entrypoint |
| Kimi / CodeBuddy / Kiro / Antigravity / OpenClaw / Hermes / Pi | generic event entrypoint plus wrapper docs, waiting for tool-specific hook wiring |
| ChatGPT Desktop / Claude Desktop | no stable public hook yet; can be wired through external automation later |

AgentLight does not implement a desktop pet, tray panel, dashboard, permission
bubbles, or terminal focus. Those remain in the original AI tool or a separate
desktop client. This project only syncs observable agent status to the hardware
red/yellow/green light.

Codex can also be monitored by reading local session files. This is useful for
verifying whether Codex activity is observable before sending anything to the
hardware:

```bash
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --from-start
scripts/codex-session-monitor --once --limit 20
```

The monitor normalizes Codex session JSONL records into:

| Output status | Source examples |
| --- | --- |
| `prompt` | `user_message` |
| `thinking` | `task_started` / `reasoning` |
| `working` | `function_call` / `web_search_call` |
| `typing` | `agent_message` / `message` |
| `success` | `task_complete` |
| `error` | `turn_aborted` |

For multiple platforms, use the configurable monitor:

```bash
scripts/multi-agent-monitor --config config/agent-monitors.example.json
scripts/multi-agent-monitor --config config/agent-monitors.example.json --send
```

The config supports:

- `file` monitors for text logs or JSONL logs
- `command` monitors that read stdout from a command
- `rules` using `contains`, `equals`, and `json_path` to map tool output into normalized events

## State Mapping

| State | Effect | Meaning |
| --- | --- | --- |
| `OFF` | All off | Disconnected or disabled |
| `GREEN` | Green steady | Idle / ready for a new task |
| `GREEN_BREATHE` | Green breathing | Connected and standing by |
| `GREEN_BLINK` | Green blinking | Manual test / heartbeat test; completion events return to `GREEN` after a short cue |
| `YELLOW` | Yellow steady | AI is executing a normal task |
| `YELLOW_BREATHE` | Yellow breathing | AI is thinking or generating for longer |
| `YELLOW_BLINK` | Yellow blinking | Tool call or command execution in progress |
| `RED` | Red steady | Error |
| `RED_BLINK` | Red blinking | Human confirmation needed / blocked |
| `RED_BREATHE` | Red breathing | Low-priority reminder / waiting for review |

## Effect Timing

| Effect | Firmware behavior |
| --- | --- |
| Startup self-test | Red, yellow, and green turn on in sequence, then all three lights blink together 3 times |
| Steady | Keeps the target color on and all other colors off |
| Blink | Default 800ms cycle, 400ms on / 400ms off; `YELLOW_BLINK` uses a 400ms cycle, 200ms on / 200ms off |
| Breathe | 2000ms cycle, brightness ramps up and then down |

The breathing effect currently uses software PWM and does not require an extra
control chip. In this build, the BS-768 board is used only as a lamp carrier
after the original current-limiting parts are removed, so keep one 220R resistor
in series between each GPIO and light control pad.

## Architecture

```text
AgentLight/
├── src/
│   ├── domain/                 Command, color, effect, and light pattern models
│   ├── application/            Status light use case and current state management
│   ├── infrastructure/         GPIO / USB serial / BLE / Wi-Fi HTTP channel implementations
│   └── main.cpp                Firmware composition root and main loop scheduling
├── agentlight_agent/
│   ├── domain/                 Desktop agent domain models: monitors, rules, runtime modes
│   ├── application/            Platform selection, monitor orchestration, service runtime use cases
│   ├── infrastructure/         JSON config, path resolution, event emission, monitor runners
│   └── interfaces/             CLI adapters behind the scripts entrypoints
├── scripts/
│   ├── agentlight              No-GUI command bridge entrypoint
│   ├── agentlight-gate         AI event mapping and duplicate suppression
│   ├── agentlight-event        Multi-agent event normalization entrypoint
│   ├── agentlight-agent        Background agent service compatibility entrypoint
│   ├── codex-session-monitor   Codex session file status monitor
│   └── multi-agent-monitor     Configurable monitor compatibility entrypoint
├── hooks/                      AI tool hook templates and integration notes
├── service/
│   ├── windows/                Windows Service Agent installers
│   └── macos/                  macOS LaunchAgent installers
├── config/
│   ├── agent-monitors.example.json      Example monitor configuration
│   ├── agentlight-agent.example.json    Example background agent service config
│   └── agent-platforms.json             Compatible AI Agent platform registry
├── tests/                      Desktop agent layering and config behavior tests
├── docs/                       Chinese user guide, compatibility, code standards, and license notes
├── platformio.ini              ESP32-C3 SuperMini firmware build config
└── CHANGELOG.md                Chinese release notes
```

Project code standards are documented in [docs/code-standards.md](./docs/code-standards.md).

Layering rules:

- `domain` does not access hardware directly
- `application` handles business semantics without knowing USB, BLE, Wi-Fi, or GPIO details
- `infrastructure` owns hardware IO, serial transport, BLE, and Wi-Fi HTTP adaptation
- `main.cpp` only wires dependencies and schedules the main loop
- `agentlight_agent/domain` defines desktop monitor models without reading files or starting processes
- `agentlight_agent/application` owns platform selection, multi-session policy, and service orchestration
- `agentlight_agent/infrastructure` owns config files, file monitoring, subprocesses, and event emission
- `agentlight_agent/interfaces` only handles CLI arguments and output; `scripts` stays backward compatible

Service runtime strategy:

- The service listens to one `activePlatform` at a time
- Switch platforms with `scripts/agentlight-agent platform set <platform>`
- Multiple projects and sessions are supported within the active platform
- Multi-session behavior does not aggregate or rotate states; it uses `latest-event-wins`
- The latest session event replaces the current light state immediately

## Build

This project uses PlatformIO with the Arduino framework.

```bash
pio run
pio run -t upload
pio device monitor
```

If USB serial does not appear, check that:

- PlatformIO's ESP32 platform is installed
- The USB cable supports data transfer
- `ARDUINO_USB_CDC_ON_BOOT=1` is enabled in `platformio.ini`

## Firmware CI

GitHub Actions builds firmware packages on `main` pushes, pull requests, `v*`
tags, and manual workflow runs.

Firmware version rules:

| Scenario | Version source |
| --- | --- |
| Push a `v*` tag | Uses the tag name, for example `v1.2026.051+1775834670` |
| Manual run with `version` | Uses the provided version |
| Normal push / PR | Generates `v1.<Year>.<DayOfYear>+<GITHUB_RUN_NUMBER>`; the trailing build number is incremented by CI |

Release versions use CalVer:

| Field | Rule | Example |
| --- | --- | --- |
| Display version | `<Major>.<Year>.<DayOfYear> (<BuildNumber>)` | `1.2026.051 (1775834670)` |
| Git tag | `v<Major>.<Year>.<DayOfYear>+<BuildNumber>` | `v1.2026.051+1775834670` |
| Short version | `<Major>.<Year>.<DayOfYear>` | `1.2026.051` |
| Build number | `<BuildNumber>` | `1775834670` |

Build channels:

| Channel | Description |
| --- | --- |
| `stable` | Formal build; GitHub Release is not marked as prerelease. `v*` tags use this by default. |
| `preview` | Preview build; GitHub Release is marked as prerelease. Normal push, PR, and manual runs use this by default. |

CI generates and publishes these standalone assets without creating an extra
zip package:

- `firmware.bin`
- `bootloader.bin`
- `partitions.bin`
- `boot_app0.bin`
- `manifest.json`
- `firmware-assets.sha256`

The firmware uses the Arduino ESP32 built-in `huge_app.csv` partition scheme
for ESP32-C3 SuperMini boards with 4MB flash. The single App partition is 3MB
so the combined USB, BLE, and Wi-Fi firmware fits without removing control
channels.

Release notes are maintained in the Chinese [CHANGELOG.md](./CHANGELOG.md). CI
reads the matching version section; if no matching section exists, it uses the
`Unreleased` section and appends the build channel, environment, Git commit,
build time, and asset list.
`manifest.json` includes the version, build channel, Git commit, SHA256 values,
and flash offsets. Release assets are written to ESP32-C3 SuperMini as
`bootloader.bin` -> `0x0000`, `partitions.bin` -> `0x8000`,
`boot_app0.bin` -> `0xe000`, and `firmware.bin` -> `0x10000`. When a `v*` tag
is pushed, or when manual release publishing is enabled, CI creates a GitHub
Release and uses the generated notes as the release body.

Preview builds do not create a GitHub Release by default, but CI prints the
Release body generated from `CHANGELOG.md` to the build log and GitHub Actions
Summary so the version notes are visible during preview runs. The Release body
is CI-only content and is not published as a firmware asset.

## Bridge Verification

Verify the multi-agent bridge with:

```bash
scripts/verify-agent-bridge
```

It checks:

- shell script syntax
- Codex session monitor Python syntax
- multi-agent name normalization
- lifecycle event normalization
- documented hook directory coverage
- multi-agent monitor example config loading

## License

AgentLight is released under the [MIT License](./LICENSE), with SPDX identifier `MIT`.
