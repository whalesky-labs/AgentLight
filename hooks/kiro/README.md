# Kiro 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent kiro --event start --send
scripts/agentlight-event --agent kiro --event tool --send
scripts/agentlight-event --agent kiro --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh kiro kiro "$@"
```

当 Kiro 暴露生命周期 Hook 时，将它们映射到最接近的归一化事件：`prompt`、`start`、`thinking`、`tool`、`typing`、`done`、`waiting` 或 `error`。
