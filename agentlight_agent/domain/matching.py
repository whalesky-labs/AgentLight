#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import json
from typing import Any

from agentlight_agent.domain.models import Monitor, MonitorFormat


def get_json_path(obj: Any, path: str) -> str:
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part)
    if current is None:
        return ""
    return str(current)


def line_value(line: str, monitor_format: MonitorFormat, json_path: str) -> str:
    if monitor_format != MonitorFormat.JSONL or not json_path:
        return line
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return ""
    return get_json_path(obj, json_path)


def match_event(line: str, monitor: Monitor) -> str:
    for rule in monitor.rules:
        value = line_value(line, monitor.format, rule.json_path)
        if rule.equals and value == rule.equals:
            return rule.event
        if rule.contains and rule.contains.lower() in value.lower():
            return rule.event
    return ""

