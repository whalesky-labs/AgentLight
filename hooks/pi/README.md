# Pi Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent pi --event start --send
scripts/agentlight-event --agent pi --event tool --send
scripts/agentlight-event --agent pi --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh pi pi "$@"
```

If Pi is not launched from a CLI, connect any available automation callback to:

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent pi --event <event> --send
```

