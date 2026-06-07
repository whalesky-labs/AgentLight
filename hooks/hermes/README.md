# Hermes Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent hermes --event start --send
scripts/agentlight-event --agent hermes --event tool --send
scripts/agentlight-event --agent hermes --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh hermes hermes "$@"
```

If Hermes runs as a background service instead of a CLI, use its lifecycle
callbacks or logs to call `scripts/agentlight-event`.

