from __future__ import annotations

from pathlib import Path

from agentlight_agent.domain.models import AgentConfig, Monitor
from agentlight_agent.infrastructure.json_config import save_agent_config


class PlatformService:
    def __init__(self, config_path: Path, config: AgentConfig, monitors: list[Monitor]) -> None:
        self._config_path = config_path
        self._config = config
        self._monitors = monitors

    def active_platform(self) -> str:
        return self._config.active_platform

    def configured_platforms(self) -> list[str]:
        return sorted({monitor.agent for monitor in self._monitors})

    def set_active_platform(self, platform: str) -> str:
        platform = platform.strip()
        if not platform:
            raise ValueError("platform set requires a platform name")
        platforms = self.configured_platforms()
        if platform not in platforms:
            raise ValueError(f"Unknown platform: {platform}. Available: {', '.join(platforms)}")
        save_agent_config(self._config_path, self._config, active_platform=platform)
        return platform

