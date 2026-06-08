from __future__ import annotations

from agentlight_agent.domain.models import Monitor
from agentlight_agent.infrastructure.monitor_runner import MonitorRunner


class MonitorService:
    def __init__(self, runner: MonitorRunner) -> None:
        self._runner = runner

    @staticmethod
    def filter_by_platform(monitors: list[Monitor], platform: str) -> list[Monitor]:
        if not platform:
            return monitors
        return [monitor for monitor in monitors if monitor.agent == platform]

    def run(
        self,
        monitors: list[Monitor],
        *,
        once: bool,
        send: bool,
        poll_interval: float,
        limit: int,
    ) -> int:
        if once:
            count = self._runner.process_existing(monitors, send=send, limit=limit)
            return 0 if count > 0 else 1
        return self._runner.run(monitors, send=send, poll_interval=poll_interval, limit=limit)

