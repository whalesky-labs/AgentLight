#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import threading
import unittest

from agentlight_agent.infrastructure.event_dispatcher import DispatchResult, LatestEventDispatcher


class LatestEventDispatcherTest(unittest.TestCase):
    def test_replaces_pending_events_while_hardware_send_is_in_progress(self) -> None:
        first_send_started = threading.Event()
        release_first_send = threading.Event()
        calls: list[list[str]] = []
        results: list[DispatchResult] = []

        def command_runner(command: list[str]) -> str:
            calls.append(command)
            if len(calls) == 1:
                first_send_started.set()
                self.assertTrue(release_first_send.wait(2), "first send did not release")
            return f"OK {command[-1]}"

        dispatcher = LatestEventDispatcher(
            "/tmp/agentlight-event",
            result_sink=results.append,
            command_runner=command_runner,
        )

        dispatcher.submit("codex", "tool", "codex-session-jsonl", send=True)
        self.assertTrue(first_send_started.wait(2), "first send did not start")
        dispatcher.submit("codex", "thinking", "codex-session-jsonl", send=True)
        dispatcher.submit("codex", "typing", "codex-session-jsonl", send=True)
        dispatcher.submit("codex", "done", "codex-session-jsonl", send=True)

        release_first_send.set()
        dispatcher.close(timeout=2)

        self.assertEqual([call[4] for call in calls], ["tool", "done"])
        self.assertEqual([result.event.event for result in results], ["tool", "done"])

    def test_keeps_pending_health_event_ahead_of_session_noise(self) -> None:
        first_send_started = threading.Event()
        release_first_send = threading.Event()
        calls: list[list[str]] = []

        def command_runner(command: list[str]) -> str:
            calls.append(command)
            if len(calls) == 1:
                first_send_started.set()
                self.assertTrue(release_first_send.wait(2), "first send did not release")
            return f"OK {command[-1]}"

        dispatcher = LatestEventDispatcher(
            "/tmp/agentlight-event",
            result_sink=lambda result: None,
            command_runner=command_runner,
        )

        dispatcher.submit("codex", "tool", "codex-session-jsonl", send=True)
        self.assertTrue(first_send_started.wait(2), "first send did not start")
        dispatcher.submit("codex", "health-waiting", "codex-desktop-health", send=True)
        dispatcher.submit("codex", "typing", "codex-session-jsonl", send=True)
        dispatcher.submit("codex", "tool", "codex-session-jsonl", send=True)

        release_first_send.set()
        dispatcher.close(timeout=2)

        self.assertEqual([call[4] for call in calls], ["tool", "health-waiting"])


if __name__ == "__main__":
    unittest.main()
