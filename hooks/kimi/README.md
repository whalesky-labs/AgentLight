# Kimi Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent kimi --event start --send
scripts/agentlight-event --agent kimi --event tool --send
scripts/agentlight-event --agent kimi --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh kimi kimi "$@"
```

If Kimi is launched by another binary or script in your environment, replace
the command after `kimi` and keep the AgentLight agent name unchanged.

