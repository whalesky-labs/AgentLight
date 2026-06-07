# CodeBuddy Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent codebuddy --event start --send
scripts/agentlight-event --agent codebuddy --event tool --send
scripts/agentlight-event --agent codebuddy --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh codebuddy codebuddy "$@"
```

When CodeBuddy provides a hook/event command, point it to:

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent codebuddy --event <event> --send
```

