# Qwen Code Integration

Use the shared event entrypoint:

```bash
scripts/agentlight-event --agent qwen --event start --send
scripts/agentlight-event --agent qwen --event tool --send
scripts/agentlight-event --agent qwen --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh qwen qwen "$@"
```

