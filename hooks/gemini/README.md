# Gemini CLI Integration

Use the shared event entrypoint:

```bash
scripts/agentlight-event --agent gemini --event start --send
scripts/agentlight-event --agent gemini --event tool --send
scripts/agentlight-event --agent gemini --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh gemini gemini "$@"
```

