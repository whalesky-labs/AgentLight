#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MonitorType(str, Enum):
    FILE = "file"
    COMMAND = "command"


class MonitorFormat(str, Enum):
    TEXT = "text"
    JSONL = "jsonl"


class MultiSessionMode(str, Enum):
    LATEST_EVENT_WINS = "latest-event-wins"


@dataclass(frozen=True)
class Rule:
    event: str
    contains: str = ""
    equals: str = ""
    json_path: str = ""


@dataclass(frozen=True)
class Monitor:
    name: str
    agent: str
    type: MonitorType
    format: MonitorFormat
    rules: tuple[Rule, ...]
    glob: str = ""
    command: tuple[str, ...] = ()
    from_start: bool = False


@dataclass(frozen=True)
class AgentConfig:
    agent_name: str
    active_platform: str
    multi_session_mode: MultiSessionMode
    monitor_config: str
    send_to_hardware: bool
    poll_interval_seconds: float
    restart_delay_seconds: float
    log_file: str
    environment: dict[str, str]

