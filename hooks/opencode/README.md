# opencode Integration

Use the shared event entrypoint:

```bash
scripts/agentlight-event --agent opencode --event start --send
scripts/agentlight-event --agent opencode --event tool --send
scripts/agentlight-event --agent opencode --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh opencode opencode "$@"
```

