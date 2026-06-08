# Hermes 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent hermes --event start --send
scripts/agentlight-event --agent hermes --event tool --send
scripts/agentlight-event --agent hermes --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh hermes hermes "$@"
```

如果 Hermes 以后台服务而不是 CLI 形式运行，可通过它的生命周期回调或日志监听调用 `scripts/agentlight-event`。
