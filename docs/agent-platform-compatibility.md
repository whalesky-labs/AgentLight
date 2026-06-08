# Agent 平台兼容矩阵

本文档用于说明 AgentLight 对主流 AI Agent 的真实接入方式。AgentLight 的定位是 ESP32-C3 硬件状态灯，不包含桌面宠物、权限气泡、托盘菜单或终端聚焦能力。

## 总体原则

- 固件只接收灯光命令：`GREEN`、`YELLOW_BLINK`、`RED_BLINK` 等。
- 桥接层把不同 AI 工具的生命周期事件归一化为：`prompt`、`start`、`thinking`、`tool`、`typing`、`done`、`waiting`、`error`、`idle`。
- 已知可读的本地会话日志优先用监听器，例如 Codex session JSONL。
- 已知可配置 Hook 的工具优先让 Hook 调用 `scripts/agentlight-event`。
- 暂无稳定公开 Hook 的工具使用 `hooks/agents/generic-wrapper.sh` 或外部自动化先接入 `start`、`done`、`error`。
- 机器可读平台清单在 `config/agent-platforms.json`，`scripts/verify-agent-bridge` 会用它校验平台名、别名、证据文件、接入方式和限制说明。

## 兼容矩阵

| 平台 | supportMode | AgentLight 当前支持方式 | 证据文件 | 当前限制 |
| --- | --- | --- | --- | --- |
| Claude Code | `event-entrypoint-or-wrapper` | 统一事件入口 + hook/wrapper 文档 | `hooks/claude/README.md`、`hooks/agents/generic-wrapper.sh` | 不自动写入 Claude 配置；权限处理仍由 Claude Code 负责。 |
| Codex CLI | `session-jsonl-monitor-and-event-entrypoint` | session JSONL 监听 + 统一事件入口 + wrapper 文档 | `scripts/codex-session-monitor`、`hooks/codex/README.md` | session 监听只读，依赖 Codex 本地 JSONL 记录。 |
| Codex Desktop | `session-jsonl-monitor-and-event-entrypoint` | session JSONL 监听 + 统一事件入口 | `scripts/codex-session-monitor`、`hooks/codex/README.md` | 不控制 Codex Desktop 界面，只观察本地可见的 Codex session 记录。 |
| GitHub Copilot CLI | `generic-wrapper` | 通用 wrapper 入口 | `hooks/copilot/README.md`、`hooks/agents/generic-wrapper.sh` | 不自动写入 `~/.copilot/hooks/hooks.json`。 |
| Gemini CLI | `generic-wrapper-or-configurable-monitor` | 通用 wrapper 入口 + 可配置日志/命令监听 | `hooks/gemini/README.md`、`scripts/multi-agent-monitor`、`config/agent-monitors.example.json` | 不自动写入 `~/.gemini/settings.json`。 |
| Antigravity CLI | `generic-wrapper-or-event-entrypoint` | 通用 wrapper 入口 | `hooks/antigravity/README.md`、`hooks/agents/generic-wrapper.sh` | 只同步状态；Antigravity 终端仍负责权限菜单。 |
| Cursor Agent | `hook-template` | Cursor Hook 模板 | `hooks/cursor/README.md`、`hooks/cursor/hooks.json.snippet`、`hooks/cursor/agent-light.sh` | 需要用户自行把配置片段合并到 Cursor Hook 配置。 |
| CodeBuddy | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/codebuddy/README.md` | 不自动写入 CodeBuddy 配置；权限处理仍由 CodeBuddy 负责。 |
| Kiro CLI | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/kiro/README.md` | 不自动创建 Kiro Agent 配置。 |
| Kimi Code CLI | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/kimi/README.md` | 不自动写入 `~/.kimi/config.toml`。 |
| Qwen Code | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/qwen/README.md` | 不自动写入 `~/.qwen/settings.json`；权限处理仍由 Qwen 负责。 |
| opencode | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/opencode/README.md` | 不自动写入 opencode 插件配置。 |
| Pi | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/pi/README.md` | 只同步能够通过回调、日志或 wrapper 接入的生命周期和工具活动。 |
| OpenClaw | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/openclaw/README.md` | 只同步状态，不提供权限气泡或终端聚焦。 |
| Hermes Agent | `event-entrypoint-or-wrapper` | 统一事件入口 + 通用 wrapper 文档 | `hooks/hermes/README.md` | 只同步能够通过回调、日志或 wrapper 接入的生命周期和工具活动。 |

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

## 项目边界

| 能力 | AgentLight 处理方式 |
| --- | --- |
| 桌面宠物动画 | 不做 |
| 托盘 / Dashboard / HUD | 不做 |
| 权限气泡 | 不做，仍交给原 AI 工具 |
| Hook / plugin 自动注册 | 暂不自动改写用户配置 |
| AI 状态同步 | 支持，输出到硬件红黄绿灯 |
| 硬件灯效 | 支持 USB、BLE、Wi-Fi HTTP |

## 验收标准

运行：

```bash
scripts/verify-agent-bridge
```

脚本会检查：

- `config/agent-platforms.json` 中登记的 15 个平台结构完整。
- 所有支持平台都能被 `scripts/agentlight-event` 归一化。
- 所有标准事件都能被归一化。
- 每个平台都有 hook 文档目录或通用接入文档。
- 兼容矩阵包含当前登记的全部平台、接入方式、证据文件和限制说明。
- Codex session monitor 和 `scripts/multi-agent-monitor` 语法可通过检查。
