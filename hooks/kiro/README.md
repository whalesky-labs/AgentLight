# Kiro Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent kiro --event start --send
scripts/agentlight-event --agent kiro --event tool --send
scripts/agentlight-event --agent kiro --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh kiro kiro "$@"
```

When Kiro exposes lifecycle hooks, wire them to `scripts/agentlight-event` with
the closest normalized event: `prompt`, `start`, `thinking`, `tool`, `typing`,
`done`, `waiting`, or `error`.

