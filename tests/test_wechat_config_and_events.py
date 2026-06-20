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

from agentlight_wechat.domain.config import ClearMode
from agentlight_wechat.domain.events import WeChatEventType
from agentlight_wechat.infrastructure.config_loader import load_wechat_config
from agentlight_wechat.infrastructure.jsonl_parser import parse_helper_line, safe_log_fields
from agentlight_wechat.interfaces.cli import DEFAULT_CONFIG, _runtime_config_path


class WeChatConfigAndEventTest(unittest.TestCase):
    def test_loads_wechat_config(self) -> None:
        config = load_wechat_config(Path("config/wechat-agentlight.example.json"))

        self.assertEqual(config.source, "wechat")
        self.assertEqual(config.clear_policy.mode, ClearMode.TIMEOUT_OR_UNREAD_CLEARED)
        self.assertEqual(config.light.blink_seconds, 10)
        self.assertEqual(config.light.refresh_seconds, 30)
        self.assertTrue(config.collection.macos_accessibility)
        self.assertEqual(config.hardware["AGENTLIGHT_TRANSPORT"], "auto")

    def test_rejects_non_wechat_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            data = json.loads(Path("config/wechat-agentlight.example.json").read_text(encoding="utf-8"))
            data["source"] = "other"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "source must be 'wechat'"):
                load_wechat_config(path)

    def test_runtime_config_prefers_installed_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            user_config = Path(tmp) / "wechat-agentlight.json"
            user_config.write_text("{}", encoding="utf-8")

            self.assertEqual(_runtime_config_path("", str(user_config)), user_config)

    def test_runtime_config_falls_back_to_example_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_user_config = Path(tmp) / "missing.json"

            self.assertEqual(_runtime_config_path("", str(missing_user_config)), DEFAULT_CONFIG)

    def test_parses_helper_jsonl_without_logging_sensitive_fields(self) -> None:
        event = parse_helper_line(
            json.dumps(
                {
                    "source": "wechat",
                    "event": "wechat-message",
                    "platform": "macos",
                    "identifier": "wxid_test_1",
                    "conversation": "秘密群",
                    "sender": "张三",
                    "summary": "银行卡密码",
                    "confidence": "visible-summary",
                    "capabilities": ["conversation-title"],
                },
                ensure_ascii=False,
            )
        )

        self.assertEqual(event.event, WeChatEventType.MESSAGE)
        self.assertEqual(event.identifier, "wxid_test_1")
        self.assertEqual(event.conversation, "秘密群")
        self.assertNotIn("秘密群", " ".join(safe_log_fields(event).values()))
        self.assertNotIn("张三", " ".join(safe_log_fields(event).values()))
        self.assertNotIn("银行卡密码", " ".join(safe_log_fields(event).values()))

    def test_navigation_unread_hint_remains_unread_signal(self) -> None:
        event = parse_helper_line(
            json.dumps(
                {
                    "source": "wechat",
                    "event": "wechat-message",
                    "platform": "macos",
                    "conversation": "微信",
                    "summary": "显示下一个未读会话",
                    "confidence": "visible-summary",
                },
                ensure_ascii=False,
            )
        )

        self.assertEqual(event.event, WeChatEventType.MESSAGE)
        self.assertEqual(event.summary, "显示下一个未读会话")


if __name__ == "__main__":
    unittest.main()
