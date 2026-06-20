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
import tempfile
import unittest
from pathlib import Path

from agentlight_wechat.application.service import WeChatService
from agentlight_wechat.domain.config import RuleConfig, WeChatConfig
from agentlight_wechat.domain.light_state import WeChatLightStateMachine
from agentlight_wechat.infrastructure.helper_runner import HelperRunner


class FakeHardware:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def send(self, command: str) -> str:
        self.commands.append(command)
        return f"OK {command.upper().replace('-', '_')}"


class StaticHelper(HelperRunner):
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def run_once(self):
        yield from self._lines


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class WeChatServiceTest(unittest.TestCase):
    def test_once_consumes_helper_event_and_sends_hardware_command(self) -> None:
        hardware = FakeHardware()
        sink: list[str] = []
        line = json.dumps({"source": "wechat", "event": "wechat-message", "platform": "macos"})
        service = WeChatService(
            Path.cwd(),
            Path("config/wechat-agentlight.example.json"),
            WeChatConfig(),
            helper_runner=StaticHelper([line]),
            hardware_runner=hardware,  # type: ignore[arg-type]
            result_sink=sink.append,
        )

        self.assertEqual(service.run_once(), 0)

        self.assertEqual(hardware.commands, ["yellow-blink"])
        self.assertIn("event=wechat-message", sink[0])
        self.assertIn("command=YELLOW_BLINK", sink[0])

    def test_rules_are_applied_before_light_state(self) -> None:
        hardware = FakeHardware()
        line = json.dumps(
            {
                "source": "wechat",
                "event": "wechat-message",
                "platform": "windows",
                "sender": "老板",
                "summary": "马上处理",
            },
            ensure_ascii=False,
        )
        service = WeChatService(
            Path.cwd(),
            Path("config/wechat-agentlight.example.json"),
            WeChatConfig(rules=RuleConfig(important_contacts=("老板",))),
            helper_runner=StaticHelper([line]),
            hardware_runner=hardware,  # type: ignore[arg-type]
            result_sink=lambda _: None,
        )

        self.assertEqual(service.run_once(), 0)

        self.assertEqual(hardware.commands, ["red-blink"])

    def test_fake_helper_can_run_without_real_wechat_or_hardware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = json.loads(Path("config/wechat-agentlight.example.json").read_text(encoding="utf-8"))
            config["helperCommand"] = ["scripts/agentlight-wechat-fake-helper", "message"]
            config["sendToHardware"] = False
            path = tmp_path / "wechat.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            service = WeChatService(
                Path.cwd(),
                path,
                WeChatConfig(send_to_hardware=False, helper_command=("scripts/agentlight-wechat-fake-helper", "message")),
                result_sink=lambda _: None,
            )

            self.assertEqual(service.run_once(), 0)

    def test_repeated_unread_event_breathes_after_blink_window(self) -> None:
        hardware = FakeHardware()
        clock = FakeClock()
        line = json.dumps({"source": "wechat", "event": "wechat-message", "platform": "macos", "summary": "新消息"})
        service = WeChatService(
            Path.cwd(),
            Path("config/wechat-agentlight.example.json"),
            WeChatConfig(),
            helper_runner=StaticHelper([line]),
            hardware_runner=hardware,  # type: ignore[arg-type]
            state_machine=WeChatLightStateMachine(blink_seconds=10, clock=clock),
            result_sink=lambda _: None,
        )

        self.assertEqual(service.run_once(), 0)
        self.assertEqual(service.run_once(), 0)
        clock.advance(10)
        self.assertEqual(service.run_once(), 0)

        self.assertEqual(hardware.commands, ["yellow-blink", "yellow-breathe"])


if __name__ == "__main__":
    unittest.main()
