# GitHub Copilot CLI Integration

Use the shared AgentLight event entrypoint:

```bash
scripts/agentlight-event --agent copilot --event start --send
scripts/agentlight-event --agent copilot --event tool --send
scripts/agentlight-event --agent copilot --event done --send
```

Wrapper pattern:

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh copilot gh copilot "$@"
```

If your Copilot setup exposes a different command name, keep the first argument
as `copilot` and replace the command after it.

