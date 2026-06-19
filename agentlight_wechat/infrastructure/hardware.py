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
import subprocess
from pathlib import Path


class HardwareCommandRunner:
    def __init__(self, command_path: Path, environment: dict[str, str]) -> None:
        self._command_path = command_path
        self._environment = environment

    def send(self, command: str) -> str:
        env = os.environ.copy()
        env.update(self._environment)
        result = subprocess.run(
            [str(self._command_path), command],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout.strip() or result.stderr.strip()
