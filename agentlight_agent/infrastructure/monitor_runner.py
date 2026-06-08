from __future__ import annotations

import glob
import os
import subprocess
import time
from pathlib import Path

from agentlight_agent.domain.matching import match_event
from agentlight_agent.domain.models import Monitor, MonitorType


class EventEmitter:
    def __init__(self, event_command: str = "scripts/agentlight-event") -> None:
        self._event_command = event_command

    def emit(self, agent: str, event: str, source: str, *, send: bool) -> None:
        command = [self._event_command, "--agent", agent, "--event", event]
        if send:
            command.append("--send")

        result = subprocess.run(command, check=False, capture_output=True, text=True)
        output = result.stdout.strip() or result.stderr.strip()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        print(f"{timestamp} mode=latest-event-wins monitor={source} {output}", flush=True)


class MonitorRunner:
    def __init__(self, emitter: EventEmitter) -> None:
        self._emitter = emitter

    def process_existing(self, monitors: list[Monitor], *, send: bool, limit: int) -> int:
        count = 0
        for monitor in monitors:
            if monitor.type == MonitorType.FILE:
                count += self._process_existing_file(monitor, send=send, limit=_remaining(limit, count))
            elif monitor.type == MonitorType.COMMAND:
                count += self._run_command_monitor(monitor, send=send, limit=_remaining(limit, count))
            if limit and count >= limit:
                return count
        return count

    def run(self, monitors: list[Monitor], *, send: bool, poll_interval: float, limit: int) -> int:
        file_monitors = [monitor for monitor in monitors if monitor.type == MonitorType.FILE]
        command_monitors = [monitor for monitor in monitors if monitor.type == MonitorType.COMMAND]

        if command_monitors:
            print("Command monitors run sequentially; file monitors run after command monitors exit.", flush=True)
            for monitor in command_monitors:
                self._run_command_monitor(monitor, send=send, limit=limit)

        return self._run_file_monitors(file_monitors, send=send, poll_interval=poll_interval, limit=limit)

    def _process_existing_file(self, monitor: Monitor, *, send: bool, limit: int) -> int:
        count = 0
        for path in _expand_files(monitor.glob):
            if not path.is_file():
                continue
            with path.open("r", encoding="utf-8", errors="replace") as file:
                for line in file:
                    event = match_event(line.strip(), monitor)
                    if not event:
                        continue
                    self._emitter.emit(monitor.agent, event, monitor.name, send=send)
                    count += 1
                    if limit and count >= limit:
                        return count
        return count

    def _run_file_monitors(self, monitors: list[Monitor], *, send: bool, poll_interval: float, limit: int) -> int:
        offsets: dict[Path, int] = {}
        count = 0
        print("AgentLight multi-agent monitor started", flush=True)
        try:
            while True:
                for monitor in monitors:
                    for path in _expand_files(monitor.glob):
                        if not path.is_file():
                            continue
                        if path not in offsets:
                            offsets[path] = 0 if monitor.from_start else path.stat().st_size
                            print(f"Watching {monitor.name}: {path}", flush=True)
                        with path.open("r", encoding="utf-8", errors="replace") as file:
                            file.seek(offsets[path])
                            for line in file:
                                event = match_event(line.strip(), monitor)
                                if not event:
                                    continue
                                self._emitter.emit(monitor.agent, event, monitor.name, send=send)
                                count += 1
                                if limit and count >= limit:
                                    return count
                            offsets[path] = file.tell()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("AgentLight multi-agent monitor stopped", flush=True)
            return count

    def _run_command_monitor(self, monitor: Monitor, *, send: bool, limit: int) -> int:
        if not monitor.command:
            return 0

        count = 0
        process = subprocess.Popen(monitor.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert process.stdout is not None
        for line in process.stdout:
            event = match_event(line.strip(), monitor)
            if not event:
                continue
            self._emitter.emit(monitor.agent, event, monitor.name, send=send)
            count += 1
            if limit and count >= limit:
                process.terminate()
                return count
        return count


def _expand_files(pattern: str) -> list[Path]:
    return [Path(path) for path in glob.glob(os.path.expanduser(pattern), recursive=True)]


def _remaining(limit: int, count: int) -> int:
    if not limit:
        return 0
    return max(0, limit - count)

