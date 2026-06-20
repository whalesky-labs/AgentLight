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
from agentlight_wechat.domain.events import WeChatEvent, WeChatEventType


def classify_event(event: WeChatEvent, rules: RuleConfig) -> WeChatEvent:
    if event.event != WeChatEventType.MESSAGE:
        return event

    muted_rule = _match_any(event.conversation, rules.muted_conversations)
    if muted_rule:
        return _replace_event(event, WeChatEventType.MUTED, f"muted:{muted_rule}")

    contact_rule = _match_any(event.sender, rules.important_contacts)
    if contact_rule:
        return _replace_event(event, WeChatEventType.IMPORTANT, f"importantContacts:{contact_rule}")

    group_rule = _match_any(event.conversation, rules.important_groups)
    if group_rule:
        return _replace_event(event, WeChatEventType.IMPORTANT, f"importantGroups:{group_rule}")

    keyword_rule = _match_any(event.summary, rules.keywords)
    if keyword_rule:
        return _replace_event(event, WeChatEventType.IMPORTANT, f"keywords:{keyword_rule}")

    if _looks_like_mention(event.summary):
        return _replace_event(event, WeChatEventType.IMPORTANT, "mention")

    return event


def _match_any(value: str, candidates: tuple[str, ...]) -> str:
    normalized = value.casefold()
    if not normalized:
        return ""
    for candidate in candidates:
        candidate = candidate.strip()
        if candidate and candidate.casefold() in normalized:
            return candidate
    return ""


def _looks_like_mention(value: str) -> bool:
    normalized = value.casefold()
    return "@我" in value or "[有人@我]" in value or "mentioned you" in normalized


def _replace_event(event: WeChatEvent, event_type: WeChatEventType, matched_rule: str) -> WeChatEvent:
    return WeChatEvent(
        event=event_type,
        platform=event.platform,
        source=event.source,
        identifier=event.identifier,
        conversation=event.conversation,
        sender=event.sender,
        summary=event.summary,
        matched_rule=matched_rule,
        confidence=event.confidence,
        timestamp=event.timestamp,
        diagnostic=event.diagnostic,
        capabilities=event.capabilities,
    )
