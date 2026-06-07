# Claude Code Integration

Use `scripts/agentlight-event` as the normalized Claude Code event entrypoint.

```bash
scripts/agentlight-event --agent claude-code --event start --send
scripts/agentlight-event --agent claude-code --event tool --send
scripts/agentlight-event --agent claude-code --event done --send
```

If your Claude Code setup exposes hooks, wire them to:

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent claude-code --event <event> --send
```

If no hook is available, wrap the CLI:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh claude-code claude "$@"
```

