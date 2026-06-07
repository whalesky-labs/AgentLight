# Antigravity Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent antigravity --event start --send
scripts/agentlight-event --agent antigravity --event tool --send
scripts/agentlight-event --agent antigravity --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh antigravity antigravity "$@"
```

If Antigravity exposes hooks or task lifecycle callbacks, call:

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent antigravity --event <event> --send
```

