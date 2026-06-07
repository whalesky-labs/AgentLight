# OpenClaw Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent openclaw --event start --send
scripts/agentlight-event --agent openclaw --event tool --send
scripts/agentlight-event --agent openclaw --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh openclaw openclaw "$@"
```

Accepted aliases include `openclaw` and `open-claw`.

