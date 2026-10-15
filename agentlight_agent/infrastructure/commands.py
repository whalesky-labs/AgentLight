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
import sys
from pathlib import Path
from collections.abc import Sequence

IS_WINDOWS = os.name == "nt"


def python_command(command: Sequence[str]) -> list[str]:
    path = Path(command[0])
    if path.is_file():
        with path.open("rb") as file:
            if b"python" in file.readline(128):
                return [os.environ.get("AGENTLIGHT_PYTHON", sys.executable), *command]
    return list(command)


def shell_command(command: Sequence[str]) -> list[str]:
    if IS_WINDOWS:
        return [os.environ.get("AGENTLIGHT_BASH", "bash"), Path(command[0]).resolve().as_posix(), *command[1:]]
    return list(command)
