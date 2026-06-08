# CodeBuddy 接入说明

使用 AgentLight 统一事件入口：

```bash
scripts/agentlight-event --agent codebuddy --event start --send
scripts/agentlight-event --agent codebuddy --event tool --send
scripts/agentlight-event --agent codebuddy --event done --send
```

Wrapper 模式：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh codebuddy codebuddy "$@"
```

如果 CodeBuddy 提供 Hook 或事件命令，将它指向：

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent codebuddy --event <event> --send
```
