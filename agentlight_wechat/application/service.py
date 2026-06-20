#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from agentlight_wechat.domain.config import WeChatConfig
from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType
from agentlight_wechat.domain.light_state import WeChatLightStateMachine
from agentlight_wechat.domain.rules import classify_event
from agentlight_wechat.infrastructure.hardware import HardwareCommandRunner
from agentlight_wechat.infrastructure.helper_runner import HelperRunner
from agentlight_wechat.infrastructure.jsonl_parser import parse_helper_line, safe_log_fields
from agentlight_wechat.infrastructure.paths import default_log_file, resolve_path


ResultSink = Callable[[str], None]


@dataclass(frozen=True)
class ProcessedEvent:
    event: WeChatEvent
    state: str
    command: str
    hardware_output: str = ""
    ignored: bool = False


class WeChatService:
    def __init__(
        self,
        repo_root: Path,
        config_path: Path,
        config: WeChatConfig,
        *,
        helper_runner: HelperRunner | None = None,
        hardware_runner: HardwareCommandRunner | None = None,
        state_machine: WeChatLightStateMachine | None = None,
        result_sink: ResultSink | None = None,
    ) -> None:
        self._repo_root = repo_root
        self._config_path = config_path
        self._config = config
        self._helper_runner = helper_runner or HelperRunner(self._helper_command())
        self._hardware_runner = hardware_runner or HardwareCommandRunner(repo_root / "scripts" / "agentlight", config.hardware)
        self._result_sink = result_sink or print
        self._state_machine = state_machine or WeChatLightStateMachine(blink_seconds=config.light.blink_seconds)

    def runtime_info(self) -> dict[str, object]:
        log_file = resolve_path(self._config.log_file or str(default_log_file()), self._config_path.parent)
        return {
            "repoRoot": str(self._repo_root),
            "config": str(self._config_path),
            "source": self._config.source,
            "platform": self._config.platform,
            "sendToHardware": self._config.send_to_hardware,
            "pollIntervalSeconds": self._config.poll_interval_seconds,
            "blinkSeconds": self._config.light.blink_seconds,
            "helperCommand": list(self._helper_command()),
            "logFile": str(log_file),
            "system": platform.system(),
        }

    def check_config(self) -> list[str]:
        info = self.runtime_info()
        return [f"{key}={value}" for key, value in info.items()]

    def doctor(self) -> list[str]:
        lines = [
            f"system={platform.system()}",
            f"config={self._config_path}",
            f"helperCommand={json.dumps(list(self._helper_command()), ensure_ascii=False)}",
            f"hardwareCommand={self._repo_root / 'scripts' / 'agentlight'}",
            f"hardwareCommandExists={(self._repo_root / 'scripts' / 'agentlight').exists()}",
        ]
        system = platform.system().lower()
        if system == "darwin":
            lines.extend(self._macos_doctor())
        elif system == "windows":
            lines.extend(self._windows_doctor())
        else:
            lines.append("wechatSupport=unsupported-system")

        try:
            first_line = next(iter(self._helper_runner.run_once()))
        except StopIteration:
            lines.append("helper=NO_OUTPUT")
        except Exception as exc:  # noqa: BLE001 - diagnostics should preserve setup errors
            lines.append(f"helper=ERROR {exc}")
        else:
            lines.append("helper=OK")
            try:
                event = parse_helper_line(first_line)
            except ValueError as exc:
                lines.append(f"helperJson=ERROR {exc}")
            else:
                fields = safe_log_fields(event)
                lines.append("lastEvent=" + " ".join(f"{key}={value}" for key, value in fields.items()))
        return lines

    def run_once(self) -> int:
        return self._run_lines(self._helper_runner.run_once(), limit=1)

    def run_forever(self) -> int:
        try:
            while True:
                self._run_lines(self._helper_runner.run_once(), limit=0)
                time.sleep(self._config.poll_interval_seconds)
        except KeyboardInterrupt:
            return 0

    def process_event(self, event: WeChatEvent) -> ProcessedEvent:
        classified = classify_event(event, self._config.rules)
        transition = self._state_machine.apply(classified)
        hardware_output = ""
        if self._config.send_to_hardware and transition.command:
            hardware_output = self._hardware_runner.send(transition.command)
        processed = ProcessedEvent(
            event=classified,
            state=transition.state.value,
            command=transition.command,
            hardware_output=hardware_output,
            ignored=transition.ignored,
        )
        self._emit(processed)
        return processed

    def _run_lines(self, lines: Iterable[str], *, limit: int) -> int:
        count = 0
        try:
            for line in lines:
                try:
                    event = parse_helper_line(line)
                except ValueError as exc:
                    event = WeChatEvent(
                        event=WeChatEventType.LISTENER_ERROR,
                        platform=platform.system().lower(),
                        diagnostic=str(exc),
                    )
                self.process_event(event)
                count += 1
                if limit and count >= limit:
                    return 0
        except Exception as exc:  # noqa: BLE001 - convert helper failures to diagnosable events
            self.process_event(
                WeChatEvent(
                    event=WeChatEventType.LISTENER_ERROR,
                    platform=platform.system().lower(),
                    diagnostic=str(exc),
                )
            )
            return 1
        return 0 if count else 1

    def _emit(self, processed: ProcessedEvent) -> None:
        fields = safe_log_fields(processed.event)
        fields["state"] = processed.state
        if processed.command:
            fields["command"] = processed.command.upper().replace("-", "_")
        if processed.ignored:
            fields["ignored"] = "true"
        if processed.hardware_output:
            fields["hardware"] = processed.hardware_output.replace("\n", "; ")
        self._result_sink(" ".join(f"{key}={value}" for key, value in fields.items() if value != ""))

    def _helper_command(self) -> tuple[str, ...]:
        if self._config.helper_command:
            return self._config.helper_command
        system = platform.system().lower()
        if system == "darwin":
            return (str(self._repo_root / "desktop" / "macos" / "AgentLightWeChatObserver.swift"), "--once")
        if system == "windows":
            return (str(self._repo_root / "desktop" / "windows" / "AgentLightWeChatObserver" / "AgentLightWeChatObserver.ps1"), "-Once")
        return (str(self._repo_root / "scripts" / "agentlight-wechat-fake-helper"), "offline")

    @staticmethod
    def _macos_doctor() -> list[str]:
        lines: list[str] = []
        lines.append(f"wechatProcess={_process_exists(['WeChat', '微信'])}")
        lines.append("accessibility=requires-user-approval")
        return lines

    @staticmethod
    def _windows_doctor() -> list[str]:
        lines: list[str] = []
        lines.append(f"wechatProcess={_process_exists(['WeChat.exe', 'Weixin.exe'])}")
        lines.append("uiAutomation=available-if-wechat-window-readable")
        return lines


def _process_exists(names: list[str]) -> str:
    system = platform.system().lower()
    try:
        if system == "darwin":
            output = subprocess.run(["pgrep", "-fl", "|".join(names)], check=False, capture_output=True, text=True)
            return "running" if output.returncode == 0 else "not-running"
        if system == "windows":
            tasklist = shutil.which("tasklist")
            if not tasklist:
                return "unknown"
            output = subprocess.run([tasklist], check=False, capture_output=True, text=True)
            data = output.stdout.casefold()
            return "running" if any(name.casefold() in data for name in names) else "not-running"
    except OSError:
        return "unknown"
    return "unknown"
