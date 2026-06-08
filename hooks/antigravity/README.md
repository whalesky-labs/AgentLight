# Antigravity 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent antigravity --event start --send
scripts/agentlight-event --agent antigravity --event tool --send
scripts/agentlight-event --agent antigravity --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh antigravity antigravity "$@"
```

如果 Antigravity 提供 Hook 或任务生命周期回调，让它调用：

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent antigravity --event <event> --send
```
