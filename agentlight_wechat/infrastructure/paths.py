#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import os
import platform
from pathlib import Path


def resolve_path(value: str, base: Path) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(value)))
    if not path.is_absolute():
        path = base / path
    return path


def default_config_path() -> Path:
    system = platform.system().lower()
    if system == "windows":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "whalesky-labs-AgentLight" / "wechat-agentlight.json"
    return Path.home() / ".whalesky-labs-AgentLight" / "wechat-agentlight.json"


def default_log_file() -> Path:
    system = platform.system().lower()
    if system == "windows":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "whalesky-labs-AgentLight" / "logs" / "agentlight-wechat.log"
    if system == "darwin":
        return Path.home() / "Library" / "Logs" / "whalesky-labs-AgentLight" / "agentlight-wechat.log"
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_home / "whalesky-labs-AgentLight" / "agentlight-wechat.log"

