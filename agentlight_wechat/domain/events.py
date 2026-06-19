#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WeChatEventType(str, Enum):
    MESSAGE = "wechat-message"
    IMPORTANT = "wechat-important"
    MUTED = "wechat-muted"
    CLEARED = "wechat-cleared"
    OFFLINE = "wechat-offline"
    LISTENER_ERROR = "wechat-listener-error"


class Confidence(str, Enum):
    UNREAD_ONLY = "unread-only"
    VISIBLE_SUMMARY = "visible-summary"
    CONVERSATION_TITLE = "conversation-title"
    MESSAGE_CONTENT_UNAVAILABLE = "message-content-unavailable"
    DIAGNOSTIC = "diagnostic"


@dataclass(frozen=True)
class WeChatEvent:
    event: WeChatEventType
    platform: str
    source: str = "wechat"
    conversation: str = ""
    sender: str = ""
    summary: str = ""
    matched_rule: str = ""
    confidence: str = Confidence.UNREAD_ONLY.value
    timestamp: str = ""
    diagnostic: str = ""
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    @property
    def sensitive_text(self) -> tuple[str, str, str]:
        return (self.conversation, self.sender, self.summary)
