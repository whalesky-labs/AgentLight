# Kimi 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent kimi --event start --send
scripts/agentlight-event --agent kimi --event tool --send
scripts/agentlight-event --agent kimi --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh kimi kimi "$@"
```

如果你的环境中 Kimi 由其他二进制或脚本启动，替换 `kimi` 后面的实际执行命令即可，AgentLight 的 Agent 名称保持 `kimi`。
