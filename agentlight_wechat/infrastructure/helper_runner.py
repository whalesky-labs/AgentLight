#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import subprocess
from collections.abc import Iterator


class HelperRunner:
    def __init__(self, command: tuple[str, ...], *, timeout_seconds: float = 10.0) -> None:
        if not command:
            raise ValueError("helper command is required")
        self._command = command
        self._timeout_seconds = timeout_seconds

    @property
    def command(self) -> tuple[str, ...]:
        return self._command

    def run_once(self) -> Iterator[str]:
        result = subprocess.run(
            self._command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self._timeout_seconds,
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        if result.returncode != 0 and not output.strip():
            raise ValueError(f"helper exited with code {result.returncode}")
        for line in output.splitlines():
            if line.strip():
                yield line.strip()

    def stream(self) -> Iterator[str]:
        process = subprocess.Popen(self._command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if line:
                yield line
