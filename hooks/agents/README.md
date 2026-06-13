# 多 Agent 接入说明

AgentLight 为所有 AI Agent 提供一个统一的状态事件入口：

```bash
scripts/agentlight-event --agent <agent> --event <event>
```

默认情况下，该命令只打印归一化后的状态。需要把事件继续发送到硬件灯时，增加 `--send`，或设置 `AGENTLIGHT_EVENT_SEND=1`，事件会进入 `scripts/agentlight-gate` 并转换为灯光状态。

## 支持的 Agent 名称

| Agent | 可接受名称 |
| --- | --- |
| Codex | `codex`, `codex-cli`, `codex-desktop` |
| Claude Code | `claude`, `claude-code` |
| Cursor Agent | `cursor`, `cursor-agent` |
| Gemini CLI | `gemini`, `gemini-cli` |
| Qwen Code | `qwen`, `qwen-code`, `qwen-cli` |
| GitHub Copilot CLI | `copilot`, `copilot-cli` |
| opencode | `opencode`, `open-code` |
| Kimi | `kimi`, `kimi-cli` |
| CodeBuddy | `codebuddy` |
| Kiro | `kiro` |
| Antigravity | `antigravity` |
| OpenClaw | `openclaw`, `open-claw` |
| Hermes | `hermes` |
| Pi | `pi` |

## 归一化事件

| 事件 | 含义 |
| --- | --- |
| `prompt` | 用户提交提示词 |
| `start` | Agent 回合或任务开始 |
| `thinking` | 模型正在推理或生成 |
| `tool` | 工具调用、Shell 命令、网页搜索或函数调用 |
| `typing` | Agent 正在输出回复文本 |
| `done` | 回合或任务成功完成 |
| `waiting` | 等待权限、审批或用户输入 |
| `error` | 中止或失败 |
| `idle` | Agent 空闲或准备就绪 |

## 示例

```bash
scripts/agentlight-event --agent codex --event task_started
scripts/agentlight-event --agent claude-code --event tool_call --send
scripts/agentlight-event cursor done
```

## Hook 策略

不同工具暴露的接入点不同：

- 有 Hook 的工具，让 Hook 调用 `scripts/agentlight-event --agent <agent> --event <event> --send`。
- 有 JSONL 会话日志的工具，用监听脚本读取，例如 `scripts/codex-session-monitor`。
- 暂无稳定 Hook 的工具，可以用 wrapper 包住 CLI 进程，至少发出 `start`、`done`、`error`。

## 平台说明

平台清单和支持方式以 `config/agent-platforms.json` 为准。

| 平台 | 接入说明 |
| --- | --- |
| Codex | `scripts/codex-session-monitor` 支持本地 session JSONL 监听。 |
| Cursor | `hooks/cursor/agent-light.sh` 用于接收 Cursor Hook 事件。 |
| Claude Code | 优先使用原生 Hook；没有 Hook 时使用 `generic-wrapper.sh`。 |
| Gemini CLI | 没有本地 Hook 或事件流时使用 `generic-wrapper.sh`。 |
| Qwen Code | 没有本地 Hook 或事件流时使用 `generic-wrapper.sh`。 |
| Copilot CLI | 用 `generic-wrapper.sh` 包住 Copilot 命令。 |
| opencode | 用 `generic-wrapper.sh` 包住 opencode 命令。 |
| Kimi / CodeBuddy / Kiro / Antigravity / OpenClaw / Hermes / Pi | 接入专用 Hook 前，先使用统一事件入口或 wrapper。 |

本项目刻意保持平台适配层很薄。AgentLight 不拥有也不重新实现各个 AI 工具，只把它们可观察到的生命周期事件归一化为固件能够理解的少量状态。

AgentLight 是硬件状态灯项目，不提供桌面宠物动画、托盘界面、Dashboard、权限气泡或终端聚焦能力。
