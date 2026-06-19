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
from typing import Any

from agentlight_wechat.domain.events import Confidence, WeChatEvent, WeChatEventType


def parse_helper_line(line: str) -> WeChatEvent:
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError("Helper output is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise ValueError("Helper output must be a JSON object")
    if str(raw.get("source", "wechat")) != "wechat":
        raise ValueError("Helper output source must be 'wechat'")

    try:
        event_type = WeChatEventType(str(raw["event"]))
    except KeyError as exc:
        raise ValueError("Helper output missing event") from exc
    except ValueError as exc:
        raise ValueError(f"Unsupported WeChat event: {raw.get('event')}") from exc

    return WeChatEvent(
        event=event_type,
        platform=_string(raw, "platform", ""),
        conversation=_string(raw, "conversation", ""),
        sender=_string(raw, "sender", ""),
        summary=_string(raw, "summary", ""),
        matched_rule=_string(raw, "matchedRule", ""),
        confidence=_string(raw, "confidence", Confidence.UNREAD_ONLY.value),
        timestamp=_string(raw, "timestamp", _string(raw, "observedAt", "")),
        diagnostic=_string(raw, "diagnostic", ""),
        capabilities=_capabilities(raw.get("capabilities", ())),
    )


def safe_log_fields(event: WeChatEvent) -> dict[str, str]:
    fields = {
        "event": event.event.value,
        "platform": event.platform,
        "confidence": event.confidence,
    }
    if event.matched_rule:
        fields["matchedRule"] = event.matched_rule
    if event.diagnostic:
        fields["diagnostic"] = event.diagnostic
    return fields


def _string(raw: dict[str, Any], key: str, default: str) -> str:
    value = raw.get(key, default)
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)
    return value


def _capabilities(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(str(item) for item in raw if str(item))
