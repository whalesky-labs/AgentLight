# Qwen Code 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent qwen --event start --send
scripts/agentlight-event --agent qwen --event tool --send
scripts/agentlight-event --agent qwen --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh qwen qwen "$@"
```
