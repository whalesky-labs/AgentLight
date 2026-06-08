# Claude Code 接入说明

使用 `scripts/agentlight-event` 作为 Claude Code 的归一化事件入口。

```bash
scripts/agentlight-event --agent claude-code --event start --send
scripts/agentlight-event --agent claude-code --event tool --send
scripts/agentlight-event --agent claude-code --event done --send
```

如果你的 Claude Code 环境暴露 Hook，将 Hook 指向：

```bash
/absolute/path/to/AgentLight/scripts/agentlight-event --agent claude-code --event <event> --send
```

如果没有 Hook，可以用 wrapper 包住 CLI：

```bash
/absolute/path/to/AgentLight/hooks/agents/generic-wrapper.sh claude-code claude "$@"
```
