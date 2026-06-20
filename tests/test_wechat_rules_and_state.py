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


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


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

    def test_muted_conversation_uses_green_light(self) -> None:
        clock = FakeClock()
        event = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", conversation="闲聊群"),
            RuleConfig(muted_conversations=("闲聊",)),
        )
        machine = WeChatLightStateMachine(blink_seconds=10, clock=clock)

        transition = machine.apply(event)
        clock.advance(10)
        sustained = machine.apply(event)

        self.assertFalse(transition.ignored)
        self.assertEqual(transition.command, "green-blink")
        self.assertEqual(transition.state, LightState.MUTED)
        self.assertEqual(sustained.command, "green-breathe")
        self.assertEqual(sustained.state, LightState.MUTED)

    def test_important_state_is_not_downgraded_by_normal_message(self) -> None:
        clock = FakeClock()
        machine = WeChatLightStateMachine(blink_seconds=10, clock=clock)

        important = machine.apply(WeChatEvent(event=WeChatEventType.IMPORTANT, platform="macos"))
        normal = machine.apply(WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos"))
        clock.advance(10)
        sustained = machine.apply(WeChatEvent(event=WeChatEventType.IMPORTANT, platform="macos"))

        self.assertEqual(important.command, "red-blink")
        self.assertEqual(normal.state, LightState.IMPORTANT)
        self.assertEqual(normal.command, "")
        self.assertEqual(sustained.command, "red-breathe")

    def test_normal_message_blinks_then_breathes(self) -> None:
        clock = FakeClock()
        machine = WeChatLightStateMachine(blink_seconds=10, refresh_seconds=30, clock=clock)
        event = WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", conversation="微信", summary="新消息")

        first = machine.apply(event)
        repeated = machine.apply(event)
        clock.advance(10)
        sustained = machine.apply(event)
        duplicate_sustained = machine.apply(event)

        self.assertEqual(first.command, "yellow-blink")
        self.assertEqual(repeated.command, "")
        self.assertEqual(sustained.command, "yellow-breathe")
        self.assertEqual(duplicate_sustained.command, "")

        clock.advance(30)
        refreshed = machine.apply(event)

        self.assertEqual(refreshed.command, "yellow-breathe")

    def test_cleared_turns_light_off(self) -> None:
        machine = WeChatLightStateMachine()
        machine.apply(WeChatEvent(event=WeChatEventType.MESSAGE, platform="windows"))

        transition = machine.apply(WeChatEvent(event=WeChatEventType.CLEARED, platform="windows"))

        self.assertEqual(transition.state, LightState.IDLE)
        self.assertEqual(transition.command, "off")


if __name__ == "__main__":
    unittest.main()
