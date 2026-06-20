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
from agentlight_wechat.domain.config import WeChatConfig
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
    def test_once_consumes_group_event_and_sends_yellow_lane_command(self) -> None:
        hardware = FakeHardware()
        sink: list[str] = []
        line = json.dumps(
            {
                "source": "wechat",
                "event": "wechat-message",
                "platform": "macos",
                "conversation": "48293083178@chatroom",
            }
        )
        service = WeChatService(
            Path.cwd(),
            Path("config/wechat-agentlight.example.json"),
            WeChatConfig(),
            helper_runner=StaticHelper([line]),
            hardware_runner=hardware,  # type: ignore[arg-type]
            result_sink=sink.append,
        )

        self.assertEqual(service.run_once(), 0)

        self.assertEqual(hardware.commands, ["LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF"])
        self.assertIn("event=wechat-message", sink[0])
        self.assertIn("category=group", sink[0])
        self.assertIn("command=LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF", sink[0])

    def test_notification_center_friend_fields_drive_green_lane(self) -> None:
        hardware = FakeHardware()
        line = json.dumps(
            {
                "source": "wechat",
                "event": "wechat-message",
                "platform": "macos",
                "identifier": "wxid_boss_1781942964_21",
                "conversation": "wxid_boss",
                "sender": "wxid_boss",
                "summary": "服务器报警",
                "confidence": "notification-center",
                "capabilities": ["notification-center", "notification-user-info"],
            },
            ensure_ascii=False,
        )
        service = WeChatService(
            Path.cwd(),
            Path("config/wechat-agentlight.example.json"),
            WeChatConfig(),
            helper_runner=StaticHelper([line]),
            hardware_runner=hardware,  # type: ignore[arg-type]
            result_sink=lambda _: None,
        )

        self.assertEqual(service.run_once(), 0)

        self.assertEqual(hardware.commands, ["LANES:RED=OFF,YELLOW=OFF,GREEN=BLINK"])

    def test_notification_center_group_fields_drive_yellow_lane(self) -> None:
        hardware = FakeHardware()
        line = json.dumps(
            {
                "source": "wechat",
                "event": "wechat-message",
                "platform": "macos",
                "identifier": "48293083178@chatroom_1781938426_1639",
                "conversation": "48293083178@chatroom",
                "sender": "48293083178@chatroom",
                "summary": "你收到了一条消息",
                "confidence": "notification-center",
                "capabilities": ["notification-center", "notification-user-info"],
            },
            ensure_ascii=False,
        )
        service = WeChatService(
            Path.cwd(),
            Path("config/wechat-agentlight.example.json"),
            WeChatConfig(),
            helper_runner=StaticHelper([line]),
            hardware_runner=hardware,  # type: ignore[arg-type]
            result_sink=lambda _: None,
        )

        self.assertEqual(service.run_once(), 0)

        self.assertEqual(hardware.commands, ["LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF"])

    def test_once_consumes_multiple_category_events_from_one_helper_run(self) -> None:
        hardware = FakeHardware()
        lines = [
            json.dumps(
                {
                    "source": "wechat",
                    "event": "wechat-message",
                    "platform": "macos",
                    "identifier": "48293083178@chatroom_1781947261_1659",
                    "conversation": "48293083178@chatroom",
                    "messageCategory": "group",
                    "confidence": "notification-history",
                }
            ),
            json.dumps(
                {
                    "source": "wechat",
                    "event": "wechat-message",
                    "platform": "macos",
                    "identifier": "wxid_friend_1781942964_21",
                    "conversation": "wxid_friend",
                    "messageCategory": "friend",
                    "confidence": "notification-history",
                }
            ),
            json.dumps(
                {
                    "source": "wechat",
                    "event": "wechat-message",
                    "platform": "macos",
                    "identifier": "qqmail_1781936375_334",
                    "conversation": "qqmail",
                    "messageCategory": "other",
                    "confidence": "notification-history",
                }
            ),
        ]
        service = WeChatService(
            Path.cwd(),
            Path("config/wechat-agentlight.example.json"),
            WeChatConfig(),
            helper_runner=StaticHelper(lines),
            hardware_runner=hardware,  # type: ignore[arg-type]
            result_sink=lambda _: None,
        )

        self.assertEqual(service.run_once(), 0)

        self.assertEqual(
            hardware.commands,
            [
                "LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF",
                "LANES:RED=OFF,YELLOW=BLINK,GREEN=BLINK",
                "LANES:RED=BLINK,YELLOW=BLINK,GREEN=BLINK",
            ],
        )

    def test_fake_helper_can_run_without_real_wechat_or_hardware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = json.loads(Path("config/wechat-agentlight.example.json").read_text(encoding="utf-8"))
            config["helperCommand"] = ["scripts/agentlight-wechat-fake-helper", "friend"]
            config["sendToHardware"] = False
            path = tmp_path / "wechat.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            service = WeChatService(
                Path.cwd(),
                path,
                WeChatConfig(send_to_hardware=False, helper_command=("scripts/agentlight-wechat-fake-helper", "friend")),
                result_sink=lambda _: None,
            )

            self.assertEqual(service.run_once(), 0)

    def test_repeated_group_event_breathes_after_blink_window(self) -> None:
        hardware = FakeHardware()
        clock = FakeClock()
        line = json.dumps(
            {
                "source": "wechat",
                "event": "wechat-message",
                "platform": "macos",
                "conversation": "48293083178@chatroom",
            }
        )
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

        self.assertEqual(
            hardware.commands,
            [
                "LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF",
                "LANES:RED=OFF,YELLOW=BREATHE,GREEN=OFF",
            ],
        )


if __name__ == "__main__":
    unittest.main()
