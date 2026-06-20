#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType


class LightState(str, Enum):
    IDLE = "idle"
    MUTED = "muted"
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


@dataclass(frozen=True)
class _UnreadLevel:
    state: LightState
    rank: int
    blink_command: str
    breathe_command: str


_UNREAD_LEVELS = {
    WeChatEventType.MUTED: _UnreadLevel(LightState.MUTED, 1, "green-blink", "green-breathe"),
    WeChatEventType.MESSAGE: _UnreadLevel(LightState.UNREAD, 2, "yellow-blink", "yellow-breathe"),
    WeChatEventType.IMPORTANT: _UnreadLevel(LightState.IMPORTANT, 3, "red-blink", "red-breathe"),
}


class WeChatLightStateMachine:
    def __init__(
        self,
        *,
        blink_seconds: float = 10.0,
        refresh_seconds: float = 30.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._state = LightState.IDLE
        self._blink_seconds = blink_seconds
        self._refresh_seconds = refresh_seconds
        self._clock = clock or time.monotonic
        self._active_level: _UnreadLevel | None = None
        self._active_fingerprint = ""
        self._blink_started_at = 0.0
        self._last_command_at = 0.0
        self._breathing = False

    @property
    def state(self) -> LightState:
        return self._state

    def apply(self, event: WeChatEvent) -> Transition:
        previous = self._state
        command = ""

        if event.event == WeChatEventType.LISTENER_ERROR:
            self._state = LightState.ERROR
            command = "red"
        elif event.event == WeChatEventType.OFFLINE:
            if self._state != LightState.ERROR:
                self._state = LightState.OFFLINE
                command = "off"
                self._clear_unread()
        elif event.event == WeChatEventType.CLEARED:
            self._state = LightState.IDLE
            command = "off"
            self._clear_unread()
        elif event.event in _UNREAD_LEVELS:
            command = self._apply_unread(event)

        changed = self._state != previous or bool(command)
        return Transition(state=self._state, command=command, changed=changed)

    def _apply_unread(self, event: WeChatEvent) -> str:
        incoming_level = _UNREAD_LEVELS[event.event]
        fingerprint = _fingerprint(event)
        now = self._clock()

        if self._active_level is not None and self._active_level.rank > incoming_level.rank:
            return self._maybe_breathe(now)

        is_new_signal = (
            self._active_level is None
            or incoming_level.rank > self._active_level.rank
            or fingerprint != self._active_fingerprint
        )
        if is_new_signal:
            self._active_level = incoming_level
            self._active_fingerprint = fingerprint
            self._blink_started_at = now
            self._last_command_at = now
            self._breathing = False
            self._state = incoming_level.state
            return incoming_level.blink_command

        self._state = incoming_level.state
        return self._maybe_breathe(now)

    def _maybe_breathe(self, now: float) -> str:
        if self._active_level is None:
            return ""
        if self._breathing:
            if now - self._last_command_at >= self._refresh_seconds:
                self._last_command_at = now
                return self._active_level.breathe_command
            return ""
        if now - self._blink_started_at < self._blink_seconds:
            return ""
        self._breathing = True
        self._last_command_at = now
        self._state = self._active_level.state
        return self._active_level.breathe_command

    def _clear_unread(self) -> None:
        self._active_level = None
        self._active_fingerprint = ""
        self._blink_started_at = 0.0
        self._last_command_at = 0.0
        self._breathing = False


def _fingerprint(event: WeChatEvent) -> str:
    parts = (event.event.value, event.conversation, event.sender, event.summary, event.confidence)
    return "\x1f".join(parts)
