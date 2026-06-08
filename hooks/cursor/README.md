# Cursor Hook 说明

本目录提供无 GUI 的 AgentLight 桥接方式，用于接收 Cursor 风格 Hook 事件。

## 文件

- `agent-light.sh`：把 Hook 事件映射到 `scripts/agentlight-gate`
- `hooks.json.snippet`：展示预期的 Hook 配置形态

## 事件映射

| Hook 事件 | AgentLight 事件 | 灯光状态 |
| --- | --- | --- |
| agent start | `start` | `YELLOW_BLINK` |
| tool call | `tool` | `YELLOW_BLINK` |
| thinking/generating | `thinking` | `YELLOW_BREATHE` |
| done | `done` | `GREEN_BLINK` |
| waiting for user | `waiting` | `RED_BLINK` |
| error | `error` | `RED` |

## 配置

1. 把 `hooks.json.snippet` 里的 `/absolute/path/to/AgentLight` 替换为本仓库路径。
2. 将片段合并到 Cursor Hook 配置中。
3. 确认 ESP32-C3 已通电，并且电脑能访问 `http://192.168.4.1`。

可以通过环境变量覆盖设备地址：

```bash
export AGENTLIGHT_BASE_URL="http://192.168.4.1"
```

手动测试：

```bash
hooks/cursor/agent-light.sh start
hooks/cursor/agent-light.sh done
```
