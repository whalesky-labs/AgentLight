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
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DispatchEvent:
    agent: str
    event: str
    source: str
    send: bool
    sequence: int


@dataclass(frozen=True)
class DispatchResult:
    event: DispatchEvent
    timestamp: str
    output: str


ResultSink = Callable[[DispatchResult], None]
CommandRunner = Callable[[list[str]], str]


class LatestEventDispatcher:
    def __init__(
        self,
        event_command: str | Path,
        *,
        result_sink: ResultSink,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self._event_command = str(event_command)
        self._result_sink = result_sink
        self._command_runner = command_runner or self._run_command
        self._condition = threading.Condition()
        self._pending: DispatchEvent | None = None
        self._sequence = 0
        self._closed = False
        self._worker = threading.Thread(target=self._run, name="agentlight-event-dispatcher", daemon=True)
        self._worker.start()

    @property
    def event_command(self) -> str:
        return self._event_command

    def submit(self, agent: str, event: str, source: str, *, send: bool) -> None:
        with self._condition:
            self._sequence += 1
            pending = DispatchEvent(
                agent=agent,
                event=event,
                source=source,
                send=send,
                sequence=self._sequence,
            )
            if self._pending is not None and _is_health_event(self._pending.event) and not _is_health_event(event):
                return
            self._pending = pending
            self._condition.notify()

    def close(self, *, drain: bool = True, timeout: float | None = None) -> None:
        if drain:
            deadline = None if timeout is None else time.monotonic() + timeout
            with self._condition:
                while self._pending is not None:
                    remaining = None if deadline is None else deadline - time.monotonic()
                    if remaining is not None and remaining <= 0:
                        break
                    self._condition.wait(remaining)

        with self._condition:
            self._closed = True
            self._condition.notify()
        self._worker.join(timeout)

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._closed:
                    self._condition.wait()
                if self._pending is None and self._closed:
                    return
                event = self._pending
                self._pending = None
                self._condition.notify_all()

            assert event is not None
            output = self._dispatch(event)
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            self._result_sink(DispatchResult(event=event, timestamp=timestamp, output=output))

    def _dispatch(self, event: DispatchEvent) -> str:
        command = [self._event_command, "--agent", event.agent, "--event", event.event]
        if event.send:
            command.append("--send")
        return self._command_runner(command)

    @staticmethod
    def _run_command(command: list[str]) -> str:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        return result.stdout.strip() or result.stderr.strip()


def _is_health_event(event: str) -> bool:
    return event.startswith("health-")
