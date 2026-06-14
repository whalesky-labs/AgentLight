#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

"""Codex Desktop connection health parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass


STATE_CHANGED_MARKER = "app_server_connection.state_changed"
FIELD_PATTERN = re.compile(r'([A-Za-z][A-Za-z0-9_]*)=("[^"]*"|\S+)')


@dataclass(frozen=True)
class CodexHealthEvent:
    status: str
    detail: str


def parse_codex_health_line(line: str, *, was_reconnecting: bool) -> CodexHealthEvent | None:
    if STATE_CHANGED_MARKER not in line:
        return None

    fields = _parse_fields(line)
    next_state = fields.get("next", "")
    previous_state = fields.get("previous", "")
    reconnect_attempt = _parse_int(fields.get("reconnectAttempt", "0"))
    reconnect_scheduled = fields.get("reconnectTimerScheduled", "").lower() == "true"
    connection_error = fields.get("connectionError", "")
    cause = fields.get("cause", "")

    if next_state == "connected" and was_reconnecting:
        return CodexHealthEvent("connected", _detail(fields))

    if next_state in {"connecting", "disconnected"} and (
        reconnect_attempt > 0
        or reconnect_scheduled
        or _has_connection_error(connection_error)
        or (previous_state == "connected" and cause not in {"stop_process", "shutdown"})
    ):
        return CodexHealthEvent("reconnecting", _detail(fields))

    return None


def _parse_fields(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, value in FIELD_PATTERN.findall(line):
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        fields[key] = value
    return fields


def _parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def _has_connection_error(value: str) -> bool:
    return bool(value and value.lower() != "null")


def _detail(fields: dict[str, str]) -> str:
    parts = []
    for key in ("cause", "previous", "next", "reconnectAttempt", "connectionError"):
        value = fields.get(key)
        if value:
            parts.append(f"{key}={value}")
    return " ".join(parts)
