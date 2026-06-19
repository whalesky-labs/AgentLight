#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import unittest

from agentlight_wechat.domain.config import RuleConfig
from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType
from agentlight_wechat.domain.light_state import LightState, WeChatLightStateMachine
from agentlight_wechat.domain.rules import classify_event


class WeChatRulesAndStateTest(unittest.TestCase):
    def test_rules_promote_important_contact(self) -> None:
        event = WeChatEvent(
            event=WeChatEventType.MESSAGE,
            platform="windows",
            sender="老板",
            summary="看一下",
        )

        classified = classify_event(event, RuleConfig(important_contacts=("老板",)))

        self.assertEqual(classified.event, WeChatEventType.IMPORTANT)
        self.assertEqual(classified.matched_rule, "importantContacts:老板")

    def test_muted_conversation_does_not_change_light(self) -> None:
        event = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", conversation="闲聊群"),
            RuleConfig(muted_conversations=("闲聊",)),
        )
        machine = WeChatLightStateMachine()

        transition = machine.apply(event)

        self.assertTrue(transition.ignored)
        self.assertEqual(transition.command, "")
        self.assertEqual(transition.state, LightState.IDLE)

    def test_important_state_is_not_downgraded_by_normal_message(self) -> None:
        machine = WeChatLightStateMachine()

        important = machine.apply(WeChatEvent(event=WeChatEventType.IMPORTANT, platform="macos"))
        normal = machine.apply(WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos"))

        self.assertEqual(important.command, "red-blink")
        self.assertEqual(normal.state, LightState.IMPORTANT)
        self.assertEqual(normal.command, "")

    def test_cleared_turns_light_off(self) -> None:
        machine = WeChatLightStateMachine()
        machine.apply(WeChatEvent(event=WeChatEventType.MESSAGE, platform="windows"))

        transition = machine.apply(WeChatEvent(event=WeChatEventType.CLEARED, platform="windows"))

        self.assertEqual(transition.state, LightState.IDLE)
        self.assertEqual(transition.command, "off")


if __name__ == "__main__":
    unittest.main()
