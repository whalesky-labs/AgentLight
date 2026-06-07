# Agent 平台兼容矩阵

本文档用于说明 AgentLight 对主流 AI Agent 的真实接入方式。它参考了 Clawd on Desk 的多 Agent 清单，但 AgentLight 的定位是 ESP32-C3 硬件状态灯，不包含桌面宠物、权限气泡、托盘菜单或终端聚焦能力。

## 总体原则

- 固件只接收灯光命令：`GREEN`、`YELLOW_BLINK`、`RED_BLINK` 等。
- 桥接层把不同 AI 工具的生命周期事件归一化为：`prompt`、`start`、`thinking`、`tool`、`typing`、`done`、`waiting`、`error`、`idle`。
- 已知可读的本地会话日志优先用监听器，例如 Codex session JSONL。
- 已知可配置 Hook 的工具优先让 Hook 调用 `scripts/agentlight-event`。
- 暂无稳定公开 Hook 的工具使用 `hooks/agents/generic-wrapper.sh` 或外部自动化先接入 `start`、`done`、`error`。

## 兼容矩阵

| 平台 | AgentLight 当前支持方式 | 证据文件 | 当前限制 |
| --- | --- | --- | --- |
| Claude Code | 统一事件入口 + hook/wrapper 文档 | `hooks/claude/README.md`、`hooks/agents/generic-wrapper.sh` | 本项目不自动写入 Claude 配置；权限确认仍由 Claude Code 自己处理 |
| Codex CLI | session JSONL 监听 + 统一事件入口 + wrapper 文档 | `scripts/codex-session-monitor`、`hooks/codex/README.md` | session 监听是只读观测；是否能捕获全部状态取决于 Codex 本地记录格式 |
| Codex Desktop | session JSONL 监听 + 统一事件入口 | `scripts/codex-session-monitor`、`hooks/codex/README.md` | 不控制 Codex Desktop UI；仅监听本机 Codex session 文件中的可见状态 |
| GitHub Copilot CLI | 通用 wrapper 入口 | `hooks/copilot/README.md`、`hooks/agents/generic-wrapper.sh` | 暂不自动写入 `~/.copilot/hooks/hooks.json` |
| Gemini CLI | 通用 wrapper 入口 + 可配置日志/命令监听 | `hooks/gemini/README.md`、`scripts/multi-agent-monitor`、`config/agent-monitors.example.json` | 暂不自动写入 `~/.gemini/settings.json` |
| Antigravity CLI | 通用 wrapper 入口 | `hooks/antigravity/README.md`、`hooks/agents/generic-wrapper.sh` | 仅做状态同步；权限菜单仍在 Antigravity 自身终端内处理 |
| Cursor Agent | Cursor Hook 模板 | `hooks/cursor/README.md`、`hooks/cursor/hooks.json.snippet`、`hooks/cursor/agent-light.sh` | 需要用户把 snippet 合并到 Cursor hook 配置 |
| CodeBuddy | 统一事件入口 + 通用 wrapper 文档 | `hooks/codebuddy/README.md` | 暂不自动写入 CodeBuddy 配置；权限确认仍由 CodeBuddy 自己处理 |
| Kiro CLI | 统一事件入口 + 通用 wrapper 文档 | `hooks/kiro/README.md` | 暂不自动创建 Kiro agent 配置 |
| Kimi Code CLI | 统一事件入口 + 通用 wrapper 文档 | `hooks/kimi/README.md` | 暂不自动写入 `~/.kimi/config.toml` |
| Qwen Code | 统一事件入口 + 通用 wrapper 文档 | `hooks/qwen/README.md` | 暂不自动写入 `~/.qwen/settings.json`；权限确认仍由 Qwen 自己处理 |
| opencode | 统一事件入口 + 通用 wrapper 文档 | `hooks/opencode/README.md` | 暂不自动写入 opencode plugin 配置 |
| Pi | 统一事件入口 + 通用 wrapper 文档 | `hooks/pi/README.md` | 仅同步可接入的生命周期/工具活动状态 |
| OpenClaw | 统一事件入口 + 通用 wrapper 文档 | `hooks/openclaw/README.md` | 仅状态同步，不处理权限气泡或终端聚焦 |
| Hermes Agent | 统一事件入口 + 通用 wrapper 文档 | `hooks/hermes/README.md` | 仅同步可接入的状态事件 |

## Codex 状态监听

Codex 是当前最适合先测试的链路，因为本项目已经实现本地 session JSONL 监听：

```bash
scripts/codex-session-monitor --once --limit 20
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --from-start
```

如果只想验证状态能否被观察到，不需要加 `--event-command`，监听器会直接打印：

```text
status=prompt
status=thinking
status=working
status=typing
status=success
status=error
```

如果要把观察到的状态接入统一事件入口，可以使用：

```bash
scripts/codex-session-monitor --thread-id "$CODEX_THREAD_ID" --event-command scripts/agentlight-event
```

再需要控制硬件时，才让事件入口加 `--send` 或设置 `AGENTLIGHT_EVENT_SEND=1`。

## 与 Clawd on Desk 的差异

| 能力 | Clawd on Desk | AgentLight |
| --- | --- | --- |
| 桌面宠物动画 | 支持 | 不做 |
| 托盘 / Dashboard / HUD | 支持 | 不做 |
| 权限气泡 | 部分 Agent 支持 | 不做，仍交给原 AI 工具 |
| Hook / plugin 自动注册 | 多平台支持 | 暂不自动改写用户配置 |
| AI 状态同步 | 支持 | 支持，输出到硬件红黄绿灯 |
| 硬件灯效 | 不涉及 | 支持 USB、BLE、Wi-Fi HTTP |

## 验收标准

运行：

```bash
scripts/verify-agent-bridge
```

脚本会检查：

- 所有支持平台都能被 `scripts/agentlight-event` 归一化。
- 所有标准事件都能被归一化。
- 每个平台都有 hook 文档目录或通用接入文档。
- 兼容矩阵包含 Clawd on Desk 清单中的全部平台。
- Codex session monitor 和 `scripts/multi-agent-monitor` 语法可通过检查。
