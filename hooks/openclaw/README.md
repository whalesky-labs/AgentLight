# OpenClaw 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent openclaw --event start --send
scripts/agentlight-event --agent openclaw --event tool --send
scripts/agentlight-event --agent openclaw --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh openclaw openclaw "$@"
```

可接受别名包括 `openclaw` 和 `open-claw`。
