#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType


class LightState(str, Enum):
    IDLE = "idle"
    UNREAD = "unread"
    IMPORTANT = "important"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass(frozen=True)
class Transition:
    state: LightState
    command: str
    changed: bool
    ignored: bool = False


class WeChatLightStateMachine:
    def __init__(self) -> None:
        self._state = LightState.IDLE

    @property
    def state(self) -> LightState:
        return self._state

    def apply(self, event: WeChatEvent) -> Transition:
        if event.event == WeChatEventType.MUTED:
            return Transition(state=self._state, command="", changed=False, ignored=True)

        previous = self._state
        command = ""

        if event.event == WeChatEventType.LISTENER_ERROR:
            self._state = LightState.ERROR
            command = "red"
        elif event.event == WeChatEventType.OFFLINE:
            if self._state != LightState.ERROR:
                self._state = LightState.OFFLINE
                command = "off"
        elif event.event == WeChatEventType.CLEARED:
            self._state = LightState.IDLE
            command = "green"
        elif event.event == WeChatEventType.IMPORTANT:
            self._state = LightState.IMPORTANT
            command = "red-blink"
        elif event.event == WeChatEventType.MESSAGE:
            if self._state != LightState.IMPORTANT:
                self._state = LightState.UNREAD
                command = "yellow-blink"

        changed = self._state != previous or bool(command)
        return Transition(state=self._state, command=command, changed=changed)
