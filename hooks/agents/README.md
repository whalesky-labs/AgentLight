# Multi-Agent Integration

AgentLight uses one normalized event entrypoint for all AI agents:

```bash
scripts/agentlight-event --agent <agent> --event <event>
```

By default it only prints normalized status. Add `--send` or set
`AGENTLIGHT_EVENT_SEND=1` to forward the event to `scripts/agentlight-gate` and
then to the light.

## Supported Agent Names

| Agent | Accepted names |
| --- | --- |
| Codex | `codex`, `codex-cli`, `codex-desktop` |
| Claude Code | `claude`, `claude-code`, `clawd` |
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

## Normalized Events

| Event | Meaning |
| --- | --- |
| `prompt` | User prompt submitted |
| `start` | Agent turn/task started |
| `thinking` | Model reasoning or generating |
| `tool` | Tool call, shell command, web search, or function call |
| `typing` | Agent response text is being produced |
| `done` | Turn/task completed successfully |
| `waiting` | Permission, approval, or human input required |
| `error` | Abort or failure |
| `idle` | Agent is idle or ready |

## Examples

```bash
scripts/agentlight-event --agent codex --event task_started
scripts/agentlight-event --agent claude-code --event tool_call --send
scripts/agentlight-event cursor done
```

## Hook Strategy

Different tools expose different integration points:

- Tools with hooks should call `scripts/agentlight-event --agent <agent> --event <event> --send`.
- Tools with JSONL session logs can be tailed by a monitor script, like `scripts/codex-session-monitor`.
- Tools without stable hooks can use a wrapper script around the CLI process to at least emit `start`, `done`, and `error`.

## Platform Notes

| Platform | Integration note |
| --- | --- |
| Codex | `scripts/codex-session-monitor` supports local session JSONL monitoring. |
| Cursor | `hooks/cursor/agent-light.sh` wraps Cursor hook events. |
| Claude Code | Use native hooks when available, otherwise `generic-wrapper.sh`. |
| Gemini CLI | Use `generic-wrapper.sh` unless a local hook/event stream is configured. |
| Qwen Code | Use `generic-wrapper.sh` unless a local hook/event stream is configured. |
| Copilot CLI | Use `generic-wrapper.sh` around the Copilot command. |
| opencode | Use `generic-wrapper.sh` around the opencode command. |
| Kimi / CodeBuddy / Kiro / Antigravity / OpenClaw / Hermes / Pi | Use the shared event entrypoint or wrapper until tool-specific hooks are connected. |

The project intentionally keeps platform adapters thin. AgentLight does not
own or reimplement each AI tool; it normalizes their lifecycle events into a
small status vocabulary that the firmware already understands.
