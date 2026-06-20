#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

from agentlight_wechat.domain.config import RuleConfig
from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType, WeChatMessageCategory


def classify_event(event: WeChatEvent, rules: RuleConfig) -> WeChatEvent:
    del rules
    if event.event not in (WeChatEventType.MESSAGE, WeChatEventType.IMPORTANT, WeChatEventType.MUTED):
        return event

    category = _classify_message_category(event)
    return _replace_event(event, category, f"category:{category}")


def _classify_message_category(event: WeChatEvent) -> str:
    if event.message_category in {item.value for item in WeChatMessageCategory}:
        return event.message_category

    searchable = " ".join(
        item
        for item in (
            event.identifier,
            event.conversation,
            event.sender,
        )
        if item
    ).casefold()

    if "@chatroom" in searchable:
        return WeChatMessageCategory.GROUP.value
    if "wxid_" in searchable:
        return WeChatMessageCategory.FRIEND.value
    return WeChatMessageCategory.OTHER.value


def _replace_event(event: WeChatEvent, category: str, matched_rule: str) -> WeChatEvent:
    return WeChatEvent(
        event=WeChatEventType.MESSAGE,
        platform=event.platform,
        source=event.source,
        identifier=event.identifier,
        conversation=event.conversation,
        sender=event.sender,
        summary=event.summary,
        message_category=category,
        matched_rule=matched_rule,
        confidence=event.confidence,
        timestamp=event.timestamp,
        diagnostic=event.diagnostic,
        capabilities=event.capabilities,
    )
