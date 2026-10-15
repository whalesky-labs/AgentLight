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
import unittest
from pathlib import Path

from agentlight_agent.domain.codex_input import CodexInputTracker
from agentlight_agent.infrastructure.json_config import load_monitors
from agentlight_agent.infrastructure.monitor_runner import EventEmitter, MonitorRunner


def record(kind: str, **fields: object) -> str:
    return json.dumps({"type": "response_item", "payload": {"type": kind, **fields}})


class CodexInputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tracker = CodexInputTracker()

    def ask(self, source: str = "one", *, asynchronous: bool = True) -> str:
        name = "request_user_input_async" if asynchronous else "request_user_input"
        return self.tracker.match(record("function_call", name=name, call_id="question"), source, "tool")

    def test_async_acceptance_and_background_work_keep_reminder(self) -> None:
        self.assertEqual(self.ask(), "waiting")
        accepted = record("function_call_output", call_id="question", output='{"accepted":true}')
        self.assertEqual(self.tracker.match(accepted, "one", "tool"), "waiting")
        self.assertEqual(self.tracker.match(record("reasoning"), "two", "thinking"), "waiting")
        self.assertEqual(self.tracker.match(record("task_complete"), "two", "done"), "waiting")

    def test_failed_async_question_does_not_leave_a_reminder(self) -> None:
        outputs = [
            'failed to parse function arguments: unknown field `question`, expected `title` or `options`',
            '{"accepted":false}',
            '{"error":"question could not be shown"}',
            '{"accepted":"true"}',
            '',
            None,
        ]
        for output in outputs:
            with self.subTest(output=output):
                self.ask()
                failed = record("function_call_output", call_id="question", output=output)
                self.assertEqual(self.tracker.match(failed, "one", "tool"), "tool")
                self.assertEqual(self.tracker.match(record("reasoning"), "two", "thinking"), "thinking")

    def test_failed_async_question_does_not_clear_another_question(self) -> None:
        first = record("function_call", name="request_user_input_async", call_id="call_failed")
        self.tracker.match(first, "one", "tool")
        second = record("function_call", name="request_user_input_async", call_id="second")
        self.tracker.match(second, "one", "tool")
        accepted = record("function_call_output", call_id="second", output='{"accepted":true}')
        self.tracker.match(accepted, "one", "tool")
        failed = record("function_call_output", call_id="call_failed", output="failed to parse function arguments")
        self.assertEqual(self.tracker.match(failed, "one", "tool"), "waiting")
        reply = record("message", role="user", content=[{"text":
            '<send_user_message_question_reply>[{"questionItemId":"second"}]</send_user_message_question_reply>'}])
        self.assertEqual(self.tracker.match(reply, "one"), "prompt")
        self.assertEqual(self.tracker.match(record("reasoning"), "two", "thinking"), "thinking")

    def test_user_answer_restores_running_state(self) -> None:
        self.ask()
        reply = record("message", role="user", content=[{"type": "input_text", "text": "answer"}])
        self.assertEqual(self.tracker.match(reply, "one"), "prompt")
        self.assertEqual(self.tracker.match(record("reasoning"), "one", "thinking"), "thinking")

    def test_answer_in_another_session_does_not_clear_pending_question(self) -> None:
        self.ask()
        reply = record("message", role="user")
        self.assertEqual(self.tracker.match(reply, "two"), "waiting")
        self.assertEqual(self.tracker.match(record("reasoning"), "one", "thinking"), "waiting")

    def test_sync_question_ends_on_its_tool_output(self) -> None:
        self.assertEqual(self.ask(asynchronous=False), "waiting")
        unrelated = record("function_call_output", call_id="other")
        self.assertEqual(self.tracker.match(unrelated, "one", "tool"), "waiting")
        answer = record("function_call_output", call_id="question")
        self.assertEqual(self.tracker.match(answer, "one", "tool"), "tool")

    def test_async_reply_only_clears_the_answered_question(self) -> None:
        self.ask()
        self.tracker.match(record("function_call", name="request_user_input_async", call_id="second"), "one")
        reply = record("message", role="user", content=[{"text":
            '<send_user_message_question_reply>[{"questionItemId":"question"}]</send_user_message_question_reply>'}])
        self.assertEqual(self.tracker.match(reply, "one"), "waiting")
        self.assertEqual(self.tracker.match(reply, "one"), "waiting")
        second_reply = record("message", role="user", content=[{"text":
            '<send_user_message_question_reply>[{"questionItemId":"second"}]</send_user_message_question_reply>'}])
        self.assertEqual(self.tracker.match(second_reply, "one"), "prompt")

    def test_aborted_turn_clears_its_question(self) -> None:
        self.ask()
        self.assertEqual(self.tracker.match(record("turn_aborted"), "one", "error"), "error")
        self.assertEqual(self.tracker.match(record("reasoning"), "one", "thinking"), "thinking")

    def test_user_prompt_and_mentioned_tool_names_do_not_trigger_reminder(self) -> None:
        message = record("message", role="user", content=[{"text": "explain request_user_input_async"}])
        self.assertEqual(self.tracker.match(message, "one"), "prompt")
        call = record("function_call", name="exec", arguments="request_user_input_async")
        self.assertEqual(self.tracker.match(call, "one", "tool"), "tool")

    def test_modern_user_message_item_clears_question(self) -> None:
        self.ask()
        reply = json.dumps({"type": "event_msg", "payload": {
            "type": "item_completed", "item": {"type": "UserMessage"},
        }})
        self.assertEqual(self.tracker.match(reply, "one"), "prompt")

    def test_background_monitor_recognizes_actual_async_tool_event(self) -> None:
        monitor = next(m for m in load_monitors(Path("config/agent-monitors.example.json"))
                       if m.name == "codex-session-jsonl")
        runner = MonitorRunner(EventEmitter())
        ask = record("function_call", name="request_user_input_async", call_id="actual-question")
        self.assertEqual(runner._match_line(ask, monitor, Path("one")), "waiting")
        self.assertEqual(runner._match_line(record("reasoning"), monitor, Path("two")), "waiting")
        self.assertEqual(runner._match_line(record("message", role="user"), monitor, Path("one")), "prompt")


if __name__ == "__main__":
    unittest.main()
