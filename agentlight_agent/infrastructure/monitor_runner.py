#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import glob
import json
import os
import subprocess
import threading
import time
from pathlib import Path

from agentlight_agent.domain.matching import match_event
from agentlight_agent.domain.codex_input import CodexInputTracker
from agentlight_agent.domain.models import Monitor, MonitorFormat, MonitorType
from agentlight_agent.infrastructure.event_dispatcher import DispatchEvent, DispatchResult, LatestEventDispatcher
from agentlight_agent.infrastructure.commands import python_command, shell_command


class EventEmitter:
    def __init__(self, event_command: str | Path = "scripts/agentlight-event") -> None:
        self._event_command = str(event_command)
        self._dispatcher: LatestEventDispatcher | None = None

    @property
    def event_command(self) -> str:
        return self._event_command

    def emit(self, agent: str, event: str, source: str, *, send: bool) -> None:
        command = [self._event_command, "--agent", agent, "--event", event]
        if send:
            command.append("--send")

        result = subprocess.run(shell_command(command), check=False, capture_output=True, text=True)
        output = result.stdout.strip() or result.stderr.strip()
        self._print_result(
            DispatchResult(
                event=_inline_event(agent, event, source, send),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                output=output,
            )
        )

    def emit_latest(self, agent: str, event: str, source: str, *, send: bool) -> None:
        if self._dispatcher is None:
            self._dispatcher = LatestEventDispatcher(self._event_command, result_sink=self._print_result)
        self._dispatcher.submit(agent, event, source, send=send)

    def close(self) -> None:
        if self._dispatcher is not None:
            self._dispatcher.close()
            self._dispatcher = None

    @staticmethod
    def _print_result(result: DispatchResult) -> None:
        print(
            f"{result.timestamp} mode=latest-event-wins monitor={result.event.source} "
            f"seq={result.event.sequence} {result.output}",
            flush=True,
        )


def _inline_event(agent: str, event: str, source: str, send: bool) -> DispatchEvent:
    return DispatchEvent(agent=agent, event=event, source=source, send=send, sequence=0)


class MonitorRunner:
    def __init__(self, emitter: EventEmitter) -> None:
        self._emitter = emitter
        self._codex_inputs = CodexInputTracker()
        self._stop = threading.Event()
        self._process_lock = threading.Lock()
        self._processes: set[subprocess.Popen] = set()

    def _match_line(self, line: str, monitor: Monitor, path: Path) -> str:
        event = match_event(line, monitor)
        if monitor.agent == "codex" and monitor.format == MonitorFormat.JSONL:
            return self._codex_inputs.match(line, str(path), event)
        return event

    def process_existing(self, monitors: list[Monitor], *, send: bool, limit: int) -> int:
        count = 0
        for monitor in monitors:
            if monitor.type == MonitorType.FILE:
                count += self._process_existing_file(monitor, send=send, limit=_remaining(limit, count))
            elif monitor.type == MonitorType.COMMAND:
                count += self._process_command_once(monitor, send=send, limit=_remaining(limit, count))
            if limit and count >= limit:
                return count
        return count

    def run(self, monitors: list[Monitor], *, send: bool, poll_interval: float, limit: int) -> int:
        file_monitors = [monitor for monitor in monitors if monitor.type == MonitorType.FILE]
        command_monitors = [monitor for monitor in monitors if monitor.type == MonitorType.COMMAND]

        command_threads: list[threading.Thread] = []
        for monitor in command_monitors:
            thread = threading.Thread(
                target=self._run_command_monitor,
                kwargs={"monitor": monitor, "send": send, "limit": limit, "latest": True},
                name=f"agentlight-monitor-{monitor.name}",
                daemon=True,
            )
            thread.start()
            command_threads.append(thread)

        try:
            if file_monitors:
                return self._run_file_monitors(file_monitors, send=send, poll_interval=poll_interval, limit=limit)
            for thread in command_threads:
                thread.join()
            return 0
        finally:
            self._stop.set()
            with self._process_lock:
                for process in self._processes:
                    if process.poll() is None:
                        process.terminate()
            for thread in command_threads:
                thread.join(timeout=3)
            self._emitter.close()

    def _process_existing_file(self, monitor: Monitor, *, send: bool, limit: int) -> int:
        count = 0
        for path in _expand_files(monitor.glob):
            if not path.is_file():
                continue
            with path.open("r", encoding="utf-8", errors="replace") as file:
                for line in file:
                    event = self._match_line(line.strip(), monitor, path)
                    if not event:
                        continue
                    self._emitter.emit(monitor.agent, event, monitor.name, send=send)
                    count += 1
                    if limit and count >= limit:
                        return count
        return count

    def _run_file_monitors(self, monitors: list[Monitor], *, send: bool, poll_interval: float, limit: int) -> int:
        offsets, count = self._restore_file_monitors(monitors, send=send)
        if limit and count >= limit:
            return count
        print("AgentLight multi-agent monitor started", flush=True)
        try:
            while not self._stop.is_set():
                for monitor in monitors:
                    for path in _expand_files(monitor.glob):
                        if not path.is_file():
                            continue
                        if path not in offsets:
                            # New files appeared after startup, so their first events are live.
                            offsets[path] = 0
                            print(f"Watching {monitor.name}: {path}", flush=True)
                        with path.open("r", encoding="utf-8", errors="replace") as file:
                            if path.stat().st_size < offsets[path]:
                                offsets[path] = 0
                            file.seek(offsets[path])
                            while True:
                                position = file.tell()
                                line = file.readline()
                                if not line or not line.endswith("\n"):
                                    file.seek(position)
                                    break
                                event = self._match_line(line.strip(), monitor, path)
                                if not event:
                                    continue
                                self._emitter.emit_latest(monitor.agent, event, monitor.name, send=send)
                                count += 1
                                if limit and count >= limit:
                                    return count
                            offsets[path] = file.tell()
                self._stop.wait(poll_interval)
        except KeyboardInterrupt:
            print("AgentLight multi-agent monitor stopped", flush=True)
            return count
        return count

    def _restore_file_monitors(self, monitors: list[Monitor], *, send: bool) -> tuple[dict[Path, int], int]:
        offsets: dict[Path, int] = {}
        latest: tuple[str, str, Monitor] | None = None
        for monitor in monitors:
            for path in _expand_files(monitor.glob):
                if not path.is_file():
                    continue
                offsets[path] = 0 if monitor.from_start else path.stat().st_size
                if monitor.from_start or monitor.agent != "codex" or monitor.format != MonitorFormat.JSONL:
                    continue
                with path.open("r", encoding="utf-8", errors="replace") as file:
                    while file.tell() < offsets[path]:
                        position = file.tell()
                        line = file.readline()
                        if not line.endswith("\n"):
                            offsets[path] = position
                            break
                        event = self._codex_inputs.match(line, str(path), match_event(line, monitor),
                                                         respect_pending=False)
                        if not event:
                            continue
                        timestamp = str(json.loads(line).get("timestamp", ""))
                        if latest is None or timestamp >= latest[0]:
                            latest = (timestamp, event, monitor)
        if latest is not None:
            _, event, monitor = latest
            self._emitter.emit_latest(monitor.agent, "waiting" if self._codex_inputs.has_pending else event,
                                      monitor.name, send=send)
            return offsets, 1
        return offsets, 0

    def _run_command_monitor(self, monitor: Monitor, *, send: bool, limit: int, latest: bool = False) -> int:
        if not monitor.command:
            return 0

        count = 0
        while not self._stop.is_set():
            try:
                process = subprocess.Popen(python_command(monitor.command), stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True)
            except OSError as exc:
                print(f"Monitor {monitor.name} failed to start: {exc}", flush=True)
                if not latest:
                    return count
                self._stop.wait(1)
                continue
            with self._process_lock:
                self._processes.add(process)
                if self._stop.is_set():
                    process.terminate()
            try:
                assert process.stdout is not None
                for line in process.stdout:
                    if self._stop.is_set():
                        break
                    event = match_event(line.strip(), monitor)
                    if not event:
                        continue
                    if latest:
                        self._emitter.emit_latest(monitor.agent, event, monitor.name, send=send)
                    else:
                        self._emitter.emit(monitor.agent, event, monitor.name, send=send)
                    count += 1
                    if limit and count >= limit:
                        return count
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                process.stdout.close()
                with self._process_lock:
                    self._processes.discard(process)
            if not latest:
                return count
            print(f"Monitor {monitor.name} exited code={process.returncode}; retrying", flush=True)
            self._stop.wait(1)
        return count

    def _process_command_once(self, monitor: Monitor, *, send: bool, limit: int) -> int:
        command = monitor.once_command or monitor.command
        if not command:
            return 0

        count = 0
        result = subprocess.run(python_command(command), check=False, capture_output=True, text=True)
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        for line in output.splitlines():
            event = match_event(line.strip(), monitor)
            if not event:
                continue
            self._emitter.emit(monitor.agent, event, monitor.name, send=send)
            count += 1
            if limit and count >= limit:
                return count
        return count


def _expand_files(pattern: str) -> list[Path]:
    return [Path(path) for path in glob.glob(os.path.expanduser(pattern), recursive=True)]


def _remaining(limit: int, count: int) -> int:
    if not limit:
        return 0
    return max(0, limit - count)
