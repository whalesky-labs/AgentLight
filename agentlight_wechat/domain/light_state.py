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
from dataclasses import dataclass, field
from enum import Enum

from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType, WeChatMessageCategory


class LightState(str, Enum):
    IDLE = "idle"
    WECHAT_UNREAD = "wechat-unread"
    OFFLINE = "offline"
    ERROR = "error"


class LaneEffect(str, Enum):
    OFF = "OFF"
    BLINK = "BLINK"
    BREATHE = "BREATHE"
    STEADY = "STEADY"


@dataclass(frozen=True)
class LightLanes:
    red: LaneEffect = LaneEffect.OFF
    yellow: LaneEffect = LaneEffect.OFF
    green: LaneEffect = LaneEffect.OFF

    def command(self) -> str:
        return f"LANES:RED={self.red.value},YELLOW={self.yellow.value},GREEN={self.green.value}"


@dataclass(frozen=True)
class Transition:
    state: LightState
    command: str
    changed: bool
    lanes: LightLanes = field(default_factory=LightLanes)
    ignored: bool = False


@dataclass
class _LaneRuntime:
    fingerprint: str = ""
    blink_started_at: float = 0.0
    last_command_at: float = 0.0
    last_weak_blink_at: float = 0.0
    effect: LaneEffect = LaneEffect.OFF


_CATEGORY_TO_LANE = {
    WeChatMessageCategory.GROUP.value: "yellow",
    WeChatMessageCategory.FRIEND.value: "green",
    WeChatMessageCategory.OTHER.value: "red",
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
        self._lanes = {
            "red": _LaneRuntime(),
            "yellow": _LaneRuntime(),
            "green": _LaneRuntime(),
        }
        self._last_lanes = LightLanes()

    @property
    def state(self) -> LightState:
        return self._state

    def apply(self, event: WeChatEvent) -> Transition:
        previous_state = self._state
        previous_lanes = self._last_lanes
        command = ""

        if event.event == WeChatEventType.LISTENER_ERROR:
            self._state = LightState.ERROR
            self._set_all_off()
            self._lanes["red"].effect = LaneEffect.STEADY
            command = self._current_lanes().command()
        elif event.event == WeChatEventType.OFFLINE:
            if self._state != LightState.ERROR:
                self._state = LightState.OFFLINE
                self._set_all_off()
                command = self._current_lanes().command()
        elif event.event == WeChatEventType.CLEARED:
            self._state = LightState.IDLE
            self._set_all_off()
            command = self._current_lanes().command()
        elif event.event in (WeChatEventType.MESSAGE, WeChatEventType.IMPORTANT, WeChatEventType.MUTED):
            command = self._apply_unread(event)

        current_lanes = self._current_lanes()
        if command:
            self._last_lanes = current_lanes
        changed = self._state != previous_state or current_lanes != previous_lanes or bool(command)
        return Transition(state=self._state, command=command, changed=changed, lanes=current_lanes)

    def _apply_unread(self, event: WeChatEvent) -> str:
        now = self._clock()
        expired = self._advance_expired_blinks(now)
        category = _message_category(event)
        lane_name = _CATEGORY_TO_LANE[category]
        lane = self._lanes[lane_name]
        fingerprint = _fingerprint(event, category)

        if lane.effect == LaneEffect.BREATHE and _is_weak_unread_signal(event):
            if now - lane.last_weak_blink_at >= self._refresh_seconds:
                self._start_blink(lane, fingerprint, now)
                self._state = LightState.WECHAT_UNREAD
                return self._current_lanes().command()
            self._state = LightState.WECHAT_UNREAD
            return self._maybe_refresh(now) or (self._current_lanes().command() if expired else "")

        if lane.effect == LaneEffect.OFF or lane.fingerprint != fingerprint:
            self._start_blink(lane, fingerprint, now)
            self._state = LightState.WECHAT_UNREAD
            return self._current_lanes().command()

        self._state = LightState.WECHAT_UNREAD
        return self._maybe_breathe_or_refresh(lane, now) or (self._current_lanes().command() if expired else "")

    def _start_blink(self, lane: _LaneRuntime, fingerprint: str, now: float) -> None:
        lane.fingerprint = fingerprint
        lane.blink_started_at = now
        lane.last_command_at = now
        lane.last_weak_blink_at = now
        lane.effect = LaneEffect.BLINK

    def _maybe_breathe_or_refresh(self, lane: _LaneRuntime, now: float) -> str:
        if lane.effect == LaneEffect.BLINK:
            if now - lane.blink_started_at < self._blink_seconds:
                return ""
            lane.effect = LaneEffect.BREATHE
            lane.last_command_at = now
            return self._current_lanes().command()

        return self._maybe_refresh(now)

    def _advance_expired_blinks(self, now: float) -> bool:
        changed = False
        for lane in self._lanes.values():
            if lane.effect == LaneEffect.BLINK and now - lane.blink_started_at >= self._blink_seconds:
                lane.effect = LaneEffect.BREATHE
                lane.last_command_at = now
                changed = True
        return changed

    def _maybe_refresh(self, now: float) -> str:
        active_lanes = [lane for lane in self._lanes.values() if lane.effect != LaneEffect.OFF]
        if not active_lanes:
            return ""
        if any(now - lane.last_command_at >= self._refresh_seconds for lane in active_lanes):
            for lane in active_lanes:
                lane.last_command_at = now
            return self._current_lanes().command()
        return ""

    def _set_all_off(self) -> None:
        for lane in self._lanes.values():
            lane.fingerprint = ""
            lane.blink_started_at = 0.0
            lane.last_command_at = 0.0
            lane.last_weak_blink_at = 0.0
            lane.effect = LaneEffect.OFF

    def _current_lanes(self) -> LightLanes:
        return LightLanes(
            red=self._lanes["red"].effect,
            yellow=self._lanes["yellow"].effect,
            green=self._lanes["green"].effect,
        )


def _message_category(event: WeChatEvent) -> str:
    if event.message_category in _CATEGORY_TO_LANE:
        return event.message_category
    return WeChatMessageCategory.OTHER.value


def _fingerprint(event: WeChatEvent, category: str) -> str:
    parts = (
        category,
        event.identifier,
        event.conversation,
        event.sender,
        event.summary,
        event.confidence,
    )
    return "\x1f".join(parts)


def _is_weak_unread_signal(event: WeChatEvent) -> bool:
    return event.confidence == "unread-only" and not event.identifier and not event.summary
