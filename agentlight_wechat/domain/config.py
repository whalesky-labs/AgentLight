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


class ClearMode(str, Enum):
    TIMEOUT = "timeout"
    UNREAD_CLEARED = "unread-cleared"
    TIMEOUT_OR_UNREAD_CLEARED = "timeout-or-unread-cleared"


@dataclass(frozen=True)
class CollectionConfig:
    macos_accessibility: bool = True
    windows_ui_automation: bool = True


@dataclass(frozen=True)
class ClearPolicy:
    mode: ClearMode = ClearMode.TIMEOUT_OR_UNREAD_CLEARED
    timeout_seconds: int = 300


@dataclass(frozen=True)
class RuleConfig:
    important_contacts: tuple[str, ...] = ()
    important_groups: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    muted_conversations: tuple[str, ...] = ()
    quiet_hours: tuple[str, ...] = ()


@dataclass(frozen=True)
class PrivacyConfig:
    store_message_content: bool = False
    log_matched_summary: bool = False


@dataclass(frozen=True)
class WeChatConfig:
    source: str = "wechat"
    platform: str = "auto"
    send_to_hardware: bool = True
    collection: CollectionConfig = field(default_factory=CollectionConfig)
    clear_policy: ClearPolicy = field(default_factory=ClearPolicy)
    rules: RuleConfig = field(default_factory=RuleConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    hardware: dict[str, str] = field(default_factory=dict)
    helper_command: tuple[str, ...] = ()
    log_file: str = ""
    poll_interval_seconds: float = 2.0
