<p align="center">
  <img src="https://avatars.githubusercontent.com/u/277389313?s=200&v=4" width="128" height="128" alt="AgentLight">
</p>

<h1 align="center">AgentLight</h1>

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
- **No-GUI bridge layer**: sends state commands through shell scripts and AI tool hooks

The complete user guide is available in Chinese at [docs/user-guide.md](./docs/user-guide.md).

## Hardware

- ESP32-C3 SuperMini
- Toy red/yellow/green light
- 220R current-limiting resistors

Default wiring:

| ESP32-C3 pin | Part |
| --- | --- |
| GPIO4 | 220R -> red LED positive |
| GPIO5 | 220R -> yellow LED positive |
| GPIO6 | 220R -> green LED positive |
| GND | LED common negative |

If the toy light is common-anode, set `AGENTLIGHT_ACTIVE_LOW=1` in
`platformio.ini` and wire the common positive to `3V3`.

## Commands

Send one command per line over USB serial, write the same text to the BLE RX
characteristic, or send commands through the Wi-Fi HTTP API.

The protocol is plain text, one command at a time:

- USB serial: terminate each command with `\n` or `\r\n`
- BLE: write the command text to the RX characteristic
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

BLE device name: `WHALESKY-LABS-AGENTLIGHT`

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
| Password | `agentlight` |
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
commands directly to the device. Wi-Fi HTTP is the default transport.

```bash
scripts/agentlight status
scripts/agentlight yellow-blink
scripts/agentlight green
scripts/agentlight red-blink
```

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
[docs/agent-service.md](./docs/agent-service.md).

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
| `done` | `GREEN_BLINK` |
| `waiting` | `RED_BLINK` |
| `error` | `RED` |

## AI Hook Integration

Stage 3 uses hooks instead of a GUI client:

- Multi-agent entrypoint: see [hooks/agents/README.md](./hooks/agents/README.md)
- Cursor: see [hooks/cursor/README.md](./hooks/cursor/README.md)
- Codex: see [hooks/codex/README.md](./hooks/codex/README.md)
- Claude Code: see [hooks/claude/README.md](./hooks/claude/README.md)
- Gemini CLI: see [hooks/gemini/README.md](./hooks/gemini/README.md)
- Qwen Code: see [hooks/qwen/README.md](./hooks/qwen/README.md)
- opencode: see [hooks/opencode/README.md](./hooks/opencode/README.md)
- Copilot CLI: see [hooks/copilot/README.md](./hooks/copilot/README.md)
- Kimi: see [hooks/kimi/README.md](./hooks/kimi/README.md)
- CodeBuddy: see [hooks/codebuddy/README.md](./hooks/codebuddy/README.md)
- Kiro: see [hooks/kiro/README.md](./hooks/kiro/README.md)
- Antigravity: see [hooks/antigravity/README.md](./hooks/antigravity/README.md)
- OpenClaw: see [hooks/openclaw/README.md](./hooks/openclaw/README.md)
- Hermes: see [hooks/hermes/README.md](./hooks/hermes/README.md)
- Pi: see [hooks/pi/README.md](./hooks/pi/README.md)

For the full platform compatibility matrix, see
[docs/agent-platform-compatibility.md](./docs/agent-platform-compatibility.md).
The matrix separates implemented monitors, hook templates, and generic wrapper
routes so the project does not overstate native integrations.

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
| `GREEN_BLINK` | Green blinking | Task completed cue / heartbeat test |
| `YELLOW` | Yellow steady | AI is executing a normal task |
| `YELLOW_BREATHE` | Yellow breathing | AI is thinking or generating for longer |
| `YELLOW_BLINK` | Yellow blinking | Tool call or command execution in progress |
| `RED` | Red steady | Error |
| `RED_BLINK` | Red blinking | Human confirmation needed / blocked |
| `RED_BREATHE` | Red breathing | Low-priority reminder / waiting for review |

## Effect Timing

| Effect | Firmware behavior |
| --- | --- |
| Steady | Keeps the target color on and all other colors off |
| Blink | 800ms cycle, 400ms on / 400ms off |
| Breathe | 2000ms cycle, brightness ramps up and then down |

The breathing effect currently uses software PWM and does not require extra
hardware. For toy lights or regular LEDs, keep a 220R resistor in series
between the GPIO pin and the LED.

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
├── docs/                       Chinese user guide, service, and compatibility documents
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
and flash offsets. When a `v*` tag is pushed, or when manual release publishing
is enabled, CI creates a GitHub Release and uses the generated notes as the
release body.

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

A Chinese license explanation is available in [docs/license.md](./docs/license.md). The repository root [LICENSE](./LICENSE) file is authoritative.
