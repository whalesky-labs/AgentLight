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
from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType, WeChatMessageCategory
from agentlight_wechat.domain.light_state import LightState, WeChatLightStateMachine
from agentlight_wechat.domain.rules import classify_event


OFF = "LANES:RED=OFF,YELLOW=OFF,GREEN=OFF"
GROUP_BLINK = "LANES:RED=OFF,YELLOW=BLINK,GREEN=OFF"
GROUP_BREATHE = "LANES:RED=OFF,YELLOW=BREATHE,GREEN=OFF"
GROUP_BREATHE_FRIEND_BLINK = "LANES:RED=OFF,YELLOW=BREATHE,GREEN=BLINK"
GROUP_FRIEND_BREATHE = "LANES:RED=OFF,YELLOW=BREATHE,GREEN=BREATHE"
ALL_THREE_ACTIVE = "LANES:RED=BLINK,YELLOW=BREATHE,GREEN=BREATHE"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class WeChatRulesAndStateTest(unittest.TestCase):
    def test_classifies_group_friend_and_other_messages(self) -> None:
        self.assertEqual(
            classify_event(
                WeChatEvent(
                    event=WeChatEventType.MESSAGE,
                    platform="macos",
                    conversation="48293083178@chatroom",
                ),
                RuleConfig(),
            ).message_category,
            WeChatMessageCategory.GROUP.value,
        )
        self.assertEqual(
            classify_event(
                WeChatEvent(
                    event=WeChatEventType.MESSAGE,
                    platform="macos",
                    identifier="wxid_j6swcwyokwtg22_1781942964_21",
                ),
                RuleConfig(),
            ).message_category,
            WeChatMessageCategory.FRIEND.value,
        )
        self.assertEqual(
            classify_event(
                WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", identifier="qqmail_1781936375_334"),
                RuleConfig(),
            ).message_category,
            WeChatMessageCategory.OTHER.value,
        )

    def test_group_message_blinks_then_breathes_yellow(self) -> None:
        clock = FakeClock()
        machine = WeChatLightStateMachine(blink_seconds=10, refresh_seconds=30, clock=clock)
        event = WeChatEvent(
            event=WeChatEventType.MESSAGE,
            platform="macos",
            conversation="48293083178@chatroom",
        )

        first = machine.apply(classify_event(event, RuleConfig()))
        repeated = machine.apply(classify_event(event, RuleConfig()))
        clock.advance(10)
        sustained = machine.apply(classify_event(event, RuleConfig()))

        self.assertEqual(first.command, GROUP_BLINK)
        self.assertEqual(repeated.command, "")
        self.assertEqual(sustained.command, GROUP_BREATHE)
        self.assertEqual(sustained.state, LightState.WECHAT_UNREAD)

    def test_friend_message_blinks_green(self) -> None:
        machine = WeChatLightStateMachine()
        event = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", conversation="wxid_friend"),
            RuleConfig(),
        )

        transition = machine.apply(event)

        self.assertEqual(transition.command, "LANES:RED=OFF,YELLOW=OFF,GREEN=BLINK")

    def test_other_message_blinks_red(self) -> None:
        machine = WeChatLightStateMachine()
        event = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", identifier="qqmail_1781936375_334"),
            RuleConfig(),
        )

        transition = machine.apply(event)

        self.assertEqual(transition.command, "LANES:RED=BLINK,YELLOW=OFF,GREEN=OFF")

    def test_group_friend_and_other_lanes_can_be_active_together(self) -> None:
        clock = FakeClock()
        machine = WeChatLightStateMachine(blink_seconds=10, clock=clock)
        group = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", conversation="48293083178@chatroom"),
            RuleConfig(),
        )
        friend = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", conversation="wxid_friend"),
            RuleConfig(),
        )
        other = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="macos", identifier="notifymessage_1_2"),
            RuleConfig(),
        )

        self.assertEqual(machine.apply(group).command, GROUP_BLINK)
        clock.advance(10)
        self.assertEqual(machine.apply(group).command, GROUP_BREATHE)
        self.assertEqual(machine.apply(friend).command, GROUP_BREATHE_FRIEND_BLINK)
        clock.advance(10)
        self.assertEqual(machine.apply(friend).command, GROUP_FRIEND_BREATHE)
        self.assertEqual(machine.apply(other).command, ALL_THREE_ACTIVE)

    def test_cleared_turns_all_lanes_off(self) -> None:
        machine = WeChatLightStateMachine()
        message = classify_event(
            WeChatEvent(event=WeChatEventType.MESSAGE, platform="windows", conversation="wxid_friend"),
            RuleConfig(),
        )
        machine.apply(message)

        transition = machine.apply(WeChatEvent(event=WeChatEventType.CLEARED, platform="windows"))

        self.assertEqual(transition.state, LightState.IDLE)
        self.assertEqual(transition.command, OFF)


if __name__ == "__main__":
    unittest.main()
