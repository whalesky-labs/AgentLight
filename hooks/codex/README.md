# Codex Hook 说明

AgentLight 不需要桌面 GUI 客户端。对 Codex 来说，只要环境中能提供稳定的生命周期 Hook、wrapper 脚本或自动化入口，就可以复用同一套脚本桥接。

多 Agent 状态归一化优先使用：

```bash
scripts/agentlight-event --agent codex --event start --send
```

如果只是观察 Codex 活动、暂时不控制硬件，可以监听 Codex 本地 session JSONL 文件。

## Session 监听器

```bash
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --from-start
scripts/codex-session-monitor --once --limit 20
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --event-command scripts/agentlight-event
```

监听器读取 `~/.codex/sessions/**/*.jsonl`，并打印归一化状态：

```text
status=prompt
status=thinking
status=working
status=typing
status=success
status=error
```

已观察到的映射关系：

| Codex session 记录 | 打印状态 |
| --- | --- |
| `event_msg.task_started` | `thinking` |
| `response_item.reasoning` | `thinking` |
| `response_item.function_call` | `working` |
| `response_item.web_search_call` | `working` |
| `event_msg.agent_message` | `typing` |
| `event_msg.task_complete` | `success` |
| `event_msg.turn_aborted` | `error` |

## 直接命令

```bash
scripts/agentlight-gate start
scripts/agentlight-gate tool
scripts/agentlight-gate thinking
scripts/agentlight-gate done
scripts/agentlight-gate waiting
scripts/agentlight-gate error
```

## Wrapper 模式

如果 Codex 工作流由 Shell 命令启动，可以这样包一层：

```bash
#!/usr/bin/env bash
set -euo pipefail

/absolute/path/to/AgentLight/scripts/agentlight-gate start

if codex "$@"; then
  /absolute/path/to/AgentLight/scripts/agentlight-gate done
else
  /absolute/path/to/AgentLight/scripts/agentlight-gate error
  exit 1
fi
```

## 推荐状态映射

| Codex 生命周期 | AgentLight 事件 | 灯光状态 |
| --- | --- | --- |
| 任务开始 | `start` | `YELLOW_BLINK` |
| 工具或命令运行中 | `tool` | `YELLOW_BLINK` |
| 模型推理或生成中 | `thinking` | `YELLOW_BREATHE` |
| 任务完成 | `done` | `GREEN_BLINK` |
| 需要用户审批或输入 | `waiting` | `RED_BLINK` |
| 任务失败 | `error` | `RED` |

如果你的环境中已经有正式 Codex Hook API，把该 Hook 指向 `scripts/agentlight-gate <event>` 即可，固件命令协议不需要变化。
