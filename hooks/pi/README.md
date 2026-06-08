# Pi 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent pi --event start --send
scripts/agentlight-event --agent pi --event tool --send
scripts/agentlight-event --agent pi --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh pi pi "$@"
```

如果 Pi 不是从 CLI 启动，可以把任何可用的自动化回调连接到：

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent pi --event <event> --send
```
