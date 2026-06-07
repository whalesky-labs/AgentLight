# Codex Hook Notes

AgentLight does not require a desktop GUI client. For Codex, use the same
script bridge whenever a stable lifecycle hook, wrapper script, or automation
entrypoint is available.

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
