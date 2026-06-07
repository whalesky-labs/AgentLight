# Cursor Hooks

This directory contains a no-GUI AgentLight bridge for Cursor-style hook events.

## Files

- `agent-light.sh` maps a hook event into `scripts/agentlight-gate`
- `hooks.json.snippet` shows the intended hook wiring shape

## Event Mapping

| Hook event | AgentLight event | Light state |
| --- | --- | --- |
| agent start | `start` | `YELLOW_BLINK` |
| tool call | `tool` | `YELLOW_BLINK` |
| thinking/generating | `thinking` | `YELLOW_BREATHE` |
| done | `done` | `GREEN_BLINK` |
| waiting for user | `waiting` | `RED_BLINK` |
| error | `error` | `RED` |

## Setup

1. Replace `/absolute/path/to/AgentLight` in `hooks.json.snippet` with this repository path.
2. Merge the snippet into your Cursor hook configuration.
3. Make sure the ESP32-C3 is powered and the computer can reach `http://192.168.4.1`.

You can override the device URL:

```bash
export AGENTLIGHT_BASE_URL="http://192.168.4.1"
```

Manual test:

```bash
hooks/cursor/agent-light.sh start
hooks/cursor/agent-light.sh done
```
