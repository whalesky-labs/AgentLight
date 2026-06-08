from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentlight_agent.domain.models import AgentConfig, Monitor, MonitorFormat, MonitorType, MultiSessionMode, Rule


def load_agent_config(path: Path) -> AgentConfig:
    if not path.exists():
        raise ValueError(f"Agent config not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "agentName",
        "activePlatform",
        "multiSessionMode",
        "monitorConfig",
        "sendToHardware",
        "pollIntervalSeconds",
        "restartDelaySeconds",
        "environment",
    }
    missing = sorted(required - raw.keys())
    if missing:
        raise ValueError(f"Agent config missing required keys: {', '.join(missing)}")

    try:
        mode = MultiSessionMode(str(raw["multiSessionMode"]))
    except ValueError as exc:
        raise ValueError("Only multiSessionMode=latest-event-wins is supported") from exc

    active_platform = _required_string(raw, "activePlatform")
    monitor_config = _required_string(raw, "monitorConfig")
    agent_name = _required_string(raw, "agentName")
    send_to_hardware = _required_bool(raw, "sendToHardware")
    poll_interval_seconds = _required_positive_float(raw, "pollIntervalSeconds")
    restart_delay_seconds = _required_positive_float(raw, "restartDelaySeconds")

    environment = raw["environment"]
    if not isinstance(environment, dict):
        raise ValueError("Agent config environment must be an object")

    return AgentConfig(
        agent_name=agent_name,
        active_platform=active_platform,
        multi_session_mode=mode,
        monitor_config=monitor_config,
        send_to_hardware=send_to_hardware,
        poll_interval_seconds=poll_interval_seconds,
        restart_delay_seconds=restart_delay_seconds,
        log_file=str(raw.get("logFile", "")),
        environment={str(key): str(value) for key, value in environment.items()},
    )


def save_agent_config(path: Path, config: AgentConfig, *, active_platform: str) -> None:
    raw = {
        "agentName": config.agent_name,
        "activePlatform": active_platform,
        "multiSessionMode": config.multi_session_mode.value,
        "monitorConfig": config.monitor_config,
        "sendToHardware": config.send_to_hardware,
        "pollIntervalSeconds": config.poll_interval_seconds,
        "restartDelaySeconds": config.restart_delay_seconds,
        "logFile": config.log_file,
        "environment": config.environment,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_monitors(path: Path) -> list[Monitor]:
    if not path.exists():
        raise ValueError(f"Monitor config not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    monitors_raw = raw.get("monitors", [])
    if not isinstance(monitors_raw, list):
        raise ValueError("Monitor config monitors must be a list")

    monitors: list[Monitor] = []
    for item in monitors_raw:
        monitors.append(_parse_monitor(item))
    return monitors


def _parse_monitor(item: dict[str, Any]) -> Monitor:
    required = {"name", "agent", "type"}
    missing = sorted(required - item.keys())
    if missing:
        raise ValueError(f"Monitor config item missing required keys: {', '.join(missing)}")

    try:
        monitor_type = MonitorType(str(item["type"]))
    except ValueError as exc:
        raise ValueError(f"Unsupported monitor type: {item['type']}") from exc

    try:
        monitor_format = MonitorFormat(str(item.get("format", "text")))
    except ValueError as exc:
        raise ValueError(f"Unsupported monitor format: {item.get('format')}") from exc

    rules = tuple(
        Rule(
            event=str(rule["event"]),
            contains=str(rule.get("contains", "")),
            equals=str(rule.get("equals", "")),
            json_path=str(rule.get("json_path", "")),
        )
        for rule in item.get("rules", [])
    )
    if not rules:
        raise ValueError(f"Monitor {item['name']} must define at least one rule")

    command_raw = item.get("command", ())
    if command_raw and not isinstance(command_raw, list):
        raise ValueError(f"Monitor {item['name']} command must be a list")
    command = tuple(str(part) for part in command_raw)
    return Monitor(
        name=str(item["name"]),
        agent=_required_string(item, "agent"),
        type=monitor_type,
        format=monitor_format,
        glob=str(item.get("glob", "")),
        command=command,
        from_start=bool(item.get("from_start", False)),
        rules=rules,
    )


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Agent config {key} must be a non-empty string")
    return value.strip()


def _required_bool(raw: dict[str, Any], key: str) -> bool:
    value = raw[key]
    if not isinstance(value, bool):
        raise ValueError(f"Agent config {key} must be a boolean")
    return value


def _required_positive_float(raw: dict[str, Any], key: str) -> float:
    value = raw[key]
    if not isinstance(value, (int, float)):
        raise ValueError(f"Agent config {key} must be a number")
    number = float(value)
    if number <= 0:
        raise ValueError(f"Agent config {key} must be greater than 0")
    return number
