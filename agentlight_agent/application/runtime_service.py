#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight
#

from __future__ import annotations

import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from agentlight_agent.domain.models import AgentConfig
from agentlight_agent.infrastructure.paths import default_log_file, resolve_path


class RuntimeService:
    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def runtime_info(self, config_path: Path, config: AgentConfig) -> dict[str, str]:
        monitor_config = resolve_path(config.monitor_config, self._repo_root)
        if not monitor_config.exists():
            raise ValueError(f"Monitor config not found: {monitor_config}")
        log_file = resolve_path(config.log_file or str(default_log_file()), config_path.parent)
        return {
            "repoRoot": str(self._repo_root),
            "config": str(config_path),
            "monitorConfig": str(monitor_config),
            "activePlatform": config.active_platform,
            "multiSessionMode": config.multi_session_mode.value,
            "logFile": str(log_file),
            "system": platform.system(),
        }

    def build_monitor_command(
        self,
        config: AgentConfig,
        *,
        once: bool,
        active_platform: str,
    ) -> list[str]:
        monitor_config = resolve_path(config.monitor_config, self._repo_root)
        if not monitor_config.exists():
            raise ValueError(f"Monitor config not found: {monitor_config}")
        command = [
            sys.executable,
            str(self._repo_root / "scripts" / "multi-agent-monitor"),
            "--config",
            str(monitor_config),
            "--poll-interval",
            str(config.poll_interval_seconds),
            "--platform",
            active_platform,
        ]
        if config.send_to_hardware:
            command.append("--send")
        if once:
            command.extend(["--once", "--limit", "1"])
        return command

    def run_agent(
        self,
        config_path: Path,
        config: AgentConfig,
        *,
        once: bool,
        platform_override: str,
    ) -> int:
        active_platform = (platform_override or config.active_platform).strip()
        if not active_platform:
            raise ValueError("Active platform is not configured")

        log_file = resolve_path(config.log_file or str(default_log_file()), config_path.parent)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(config.environment)
        env["AGENTLIGHT_AGENT_CONFIG"] = str(config_path)
        env["PYTHONUNBUFFERED"] = "1"

        command = self.build_monitor_command(config, once=once, active_platform=active_platform)

        with log_file.open("a", encoding="utf-8", buffering=1) as log:
            self._log_line(
                log,
                f"AgentLight agent starting platform={active_platform} "
                f"mode={config.multi_session_mode.value} command={command}",
            )
            while True:
                process = subprocess.Popen(
                    command,
                    cwd=str(self._repo_root),
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                return_code = process.wait()
                self._log_line(log, f"AgentLight monitor exited code={return_code}")
                if once:
                    return 0
                time.sleep(config.restart_delay_seconds)
                self._log_line(log, "Restarting AgentLight monitor")

    @staticmethod
    def _log_line(file, message: str) -> None:
        timestamp = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        file.write(f"{timestamp} {message}\n")
        file.flush()

