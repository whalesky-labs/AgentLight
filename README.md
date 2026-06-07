# AgentLight Firmware

AgentLight is an ESP32-C3 firmware project for a small desktop AI status light.
It supports USB serial and BLE commands so a desktop bridge can show AI task
state on a toy traffic light.

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

Send one command per line over USB serial, or write the same text to the BLE RX
characteristic.

| Command | Result |
| --- | --- |
| `GREEN` | Green on, red/yellow off |
| `YELLOW` | Yellow on, red/green off |
| `RED` | Red on, yellow/green off |
| `OFF` | All lights off |
| `PING` | Responds `PONG` |
| `STATUS` | Responds with the current light state |
| `HELP` | Responds with supported commands |

BLE device name: `AgentLight`

BLE service and characteristics:

| Item | UUID |
| --- | --- |
| Service | `8f16d7a0-6c6d-4d68-8d64-6b4d2a86b601` |
| RX write | `8f16d7a1-6c6d-4d68-8d64-6b4d2a86b601` |
| TX notify/read | `8f16d7a2-6c6d-4d68-8d64-6b4d2a86b601` |

## Build

This project uses PlatformIO with the Arduino framework.

```bash
pio run
pio run -t upload
pio device monitor
```

If USB serial does not appear, install PlatformIO's ESP32 platform and make
sure the board is connected with a data-capable USB cable.

