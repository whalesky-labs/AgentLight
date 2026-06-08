from __future__ import annotations

import os
import platform
from pathlib import Path


def resolve_path(value: str, base: Path) -> Path:
    path = Path(os.path.expanduser(value))
    if not path.is_absolute():
        path = base / path
    return path


def default_log_file() -> Path:
    system = platform.system().lower()
    if system == "windows":
        root = Path(os.environ.get("ProgramData", "C:/ProgramData"))
        return root / "whalesky-labs-AgentLight" / "logs" / "agentlight-agent.log"
    if system == "darwin":
        return Path.home() / "Library" / "Logs" / "whalesky-labs-AgentLight" / "agentlight-agent.log"
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_home / "whalesky-labs-AgentLight" / "agentlight-agent.log"

