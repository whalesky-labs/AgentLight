# GitHub Copilot CLI 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent copilot --event start --send
scripts/agentlight-event --agent copilot --event tool --send
scripts/agentlight-event --agent copilot --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh copilot gh copilot "$@"
```

如果你的 Copilot 环境使用其他命令名，保持第一个参数为 `copilot`，只替换它后面的实际执行命令。
