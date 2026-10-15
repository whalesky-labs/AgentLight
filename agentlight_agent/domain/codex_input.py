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


class CodexInputTracker:
    """Keep unanswered questions visible while other sessions continue working."""

    def __init__(self) -> None:
        self._pending: dict[str, dict[str, bool]] = {}

    @property
    def has_pending(self) -> bool:
        return bool(self._pending)

    def match(self, line: str, source: str, fallback: str = "", *, respect_pending: bool = True) -> str:
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            return fallback
        if not isinstance(obj, dict) or obj.get("type") not in {"response_item", "event_msg"}:
            return fallback
        payload = obj.get("payload")
        if not isinstance(payload, dict):
            return fallback
        kind = payload.get("type")
        transition = ""
        if kind in {"function_call", "custom_tool_call"}:
            name = str(payload.get("name", "")).rsplit(".", 1)[-1]
            if name in {"request_user_input", "request_user_input_async"}:
                call_id = str(payload.get("call_id") or payload.get("id") or name)
                self._pending.setdefault(source, {})[call_id] = name.endswith("_async")
                transition = "waiting"
        elif kind in {"function_call_output", "custom_tool_call_output"}:
            pending = self._pending.get(source, {})
            call_id = str(payload.get("call_id", ""))
            # Only accepted async questions can still need an answer after tool output.
            if call_id in pending and (
                not pending[call_id] or not _async_question_accepted(payload.get("output"))
            ):
                del pending[call_id]
                transition = "tool"
        elif (
            kind == "user_message"
            or (kind == "message" and payload.get("role") == "user")
            or (kind == "item_completed" and (payload.get("item") or {}).get("type") == "UserMessage")
        ):
            item = payload.get("item") or payload
            content = json.dumps(item.get("content", payload.get("message", "")), ensure_ascii=False)
            if "<send_user_message_question_reply>" in content:
                pending = self._pending.get(source, {})
                for call_id in list(pending):
                    if call_id in content:
                        del pending[call_id]
            else:
                self._pending.pop(source, None)
            transition = "prompt"
        elif kind == "turn_aborted":
            self._pending.pop(source, None)
        if source in self._pending and not self._pending[source]:
            del self._pending[source]
        if respect_pending and self._pending and (transition or fallback):
            return "waiting"
        return transition or fallback


def _async_question_accepted(output: object) -> bool:
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except ValueError:
            return False
    return isinstance(output, dict) and output.get("accepted") is True
