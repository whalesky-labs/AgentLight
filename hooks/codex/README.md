# Codex Hook Notes

AgentLight does not require a desktop GUI client. For Codex, use the same
script bridge whenever a stable lifecycle hook, wrapper script, or automation
entrypoint is available.

You can also monitor Codex activity without controlling the hardware by tailing
Codex's local session JSONL files.

## Session Monitor

```bash
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --from-start
scripts/codex-session-monitor --once --limit 20
```

The monitor reads `~/.codex/sessions/**/*.jsonl` and prints normalized status
lines:

```text
status=prompt
status=thinking
status=working
status=typing
status=success
status=error
```

Observed mappings:

| Codex session record | Printed status |
| --- | --- |
| `event_msg.task_started` | `thinking` |
| `response_item.reasoning` | `thinking` |
| `response_item.function_call` | `working` |
| `response_item.web_search_call` | `working` |
| `event_msg.agent_message` | `typing` |
| `event_msg.task_complete` | `success` |
| `event_msg.turn_aborted` | `error` |

## Direct Commands

```bash
scripts/agentlight-gate start
scripts/agentlight-gate tool
scripts/agentlight-gate thinking
scripts/agentlight-gate done
scripts/agentlight-gate waiting
scripts/agentlight-gate error
```

## Wrapper Pattern

If a Codex workflow is launched by a shell command, wrap it like this:

```bash
#!/usr/bin/env bash
set -euo pipefail

/absolute/path/to/AgentLight/scripts/agentlight-gate start

if codex "$@"; then
  /absolute/path/to/AgentLight/scripts/agentlight-gate done
else
  /absolute/path/to/AgentLight/scripts/agentlight-gate error
  exit 1
fi
```

## Recommended State Mapping

| Codex lifecycle | AgentLight event | Light state |
| --- | --- | --- |
| task starts | `start` | `YELLOW_BLINK` |
| tool/command is running | `tool` | `YELLOW_BLINK` |
| model is thinking/generating | `thinking` | `YELLOW_BREATHE` |
| task completes | `done` | `GREEN_BLINK` |
| needs user approval/input | `waiting` | `RED_BLINK` |
| task fails | `error` | `RED` |

When a first-class Codex hook API is available in your environment, point that
hook to `scripts/agentlight-gate <event>` and keep the firmware protocol
unchanged.
