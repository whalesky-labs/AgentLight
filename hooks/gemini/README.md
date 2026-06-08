# Gemini CLI 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent gemini --event start --send
scripts/agentlight-event --agent gemini --event tool --send
scripts/agentlight-event --agent gemini --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh gemini gemini "$@"
```
