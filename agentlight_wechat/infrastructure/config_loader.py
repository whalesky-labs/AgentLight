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
from pathlib import Path
from typing import Any

from agentlight_wechat.domain.config import (
    ClearMode,
    ClearPolicy,
    CollectionConfig,
    LightConfig,
    PrivacyConfig,
    RuleConfig,
    WeChatConfig,
)


def load_wechat_config(path: Path) -> WeChatConfig:
    if not path.exists():
        raise ValueError(f"WeChat config not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("WeChat config must be an object")

    source = _string(raw, "source", "wechat")
    if source != "wechat":
        raise ValueError("WeChat config source must be 'wechat'")

    return WeChatConfig(
        source=source,
        platform=_string(raw, "platform", "auto"),
        send_to_hardware=_bool(raw, "sendToHardware", True),
        collection=_collection(raw.get("collection", {})),
        clear_policy=_clear_policy(raw.get("clearPolicy", {})),
        light=_light(raw.get("light", {})),
        rules=_rules(raw.get("rules", {})),
        privacy=_privacy(raw.get("privacy", {})),
        hardware=_string_dict(raw.get("hardware", {}), "hardware"),
        helper_command=_string_tuple(raw.get("helperCommand", ()), "helperCommand"),
        log_file=_string(raw, "logFile", ""),
        poll_interval_seconds=_positive_float(raw, "pollIntervalSeconds", 2.0),
    )


def _collection(raw: Any) -> CollectionConfig:
    raw = _object(raw, "collection")
    return CollectionConfig(
        macos_accessibility=_bool(raw, "macosAccessibility", True),
        windows_ui_automation=_bool(raw, "windowsUiAutomation", True),
    )


def _clear_policy(raw: Any) -> ClearPolicy:
    raw = _object(raw, "clearPolicy")
    try:
        mode = ClearMode(_string(raw, "mode", ClearMode.TIMEOUT_OR_UNREAD_CLEARED.value))
    except ValueError as exc:
        raise ValueError(f"Unsupported clearPolicy.mode: {raw.get('mode')}") from exc
    timeout_seconds = _int(raw, "timeoutSeconds", 300)
    if timeout_seconds <= 0:
        raise ValueError("clearPolicy.timeoutSeconds must be greater than 0")
    return ClearPolicy(mode=mode, timeout_seconds=timeout_seconds)


def _light(raw: Any) -> LightConfig:
    raw = _object(raw, "light")
    return LightConfig(
        blink_seconds=_positive_float(raw, "blinkSeconds", 10.0),
        refresh_seconds=_positive_float(raw, "refreshSeconds", 30.0),
    )


def _rules(raw: Any) -> RuleConfig:
    raw = _object(raw, "rules")
    return RuleConfig(
        quiet_hours=_string_tuple(raw.get("quietHours", ()), "quietHours"),
    )


def _privacy(raw: Any) -> PrivacyConfig:
    raw = _object(raw, "privacy")
    return PrivacyConfig(
        store_message_content=_bool(raw, "storeMessageContent", False),
        log_matched_summary=_bool(raw, "logMatchedSummary", False),
    )


def _object(raw: Any, name: str) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"WeChat config {name} must be an object")
    return raw


def _string(raw: dict[str, Any], key: str, default: str) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"WeChat config {key} must be a string")
    return value.strip()


def _bool(raw: dict[str, Any], key: str, default: bool) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"WeChat config {key} must be a boolean")
    return value


def _int(raw: dict[str, Any], key: str, default: int) -> int:
    value = raw.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"WeChat config {key} must be an integer")
    return value


def _positive_float(raw: dict[str, Any], key: str, default: float) -> float:
    value = raw.get(key, default)
    if not isinstance(value, (int, float)):
        raise ValueError(f"WeChat config {key} must be a number")
    number = float(value)
    if number <= 0:
        raise ValueError(f"WeChat config {key} must be greater than 0")
    return number


def _string_tuple(raw: Any, name: str) -> tuple[str, ...]:
    if raw in (None, ""):
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"WeChat config {name} must be a list")
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise ValueError(f"WeChat config {name} must contain only strings")
        if item.strip():
            values.append(item.strip())
    return tuple(values)


def _string_dict(raw: Any, name: str) -> dict[str, str]:
    raw = _object(raw, name)
    return {str(key): str(value) for key, value in raw.items()}
