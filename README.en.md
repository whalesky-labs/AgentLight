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
serial, Bluetooth LE, and Wi-Fi HTTP commands so Codex, ChatGPT, Claude,
Cursor, and other AI workflows can show task state on a toy traffic light.

This repository contains two parts:

- **ESP32-C3 firmware**: receives commands and controls the red/yellow/green lights
- **No-GUI bridge layer**: sends state commands through shell scripts and AI tool hooks

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

## Event Gate

`scripts/agentlight-gate` receives AI lifecycle events and applies lightweight
deduplication.

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

- Cursor: see [hooks/cursor/README.md](./hooks/cursor/README.md)
- Codex: see [hooks/codex/README.md](./hooks/codex/README.md)

All hooks eventually call the same entrypoint:

```bash
scripts/agentlight-gate <event>
```

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
src/domain            Command, color, effect, and light pattern models
src/application       Status light use case and current state management
src/infrastructure    GPIO / USB serial / BLE / Wi-Fi HTTP channel implementations
src/main.cpp          Firmware composition root and main loop scheduling
scripts/              No-GUI command bridge and event gate
hooks/                AI tool hook templates and integration notes
```

Layering rules:

- `domain` does not access hardware directly
- `application` handles business semantics without knowing USB, BLE, Wi-Fi, or GPIO details
- `infrastructure` owns hardware IO, serial transport, BLE, and Wi-Fi HTTP adaptation
- `main.cpp` only wires dependencies and schedules the main loop

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
