#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import unittest

from agentlight_agent.domain.codex_health import parse_codex_health_line


class CodexHealthTest(unittest.TestCase):
    def test_recovery_clears_state_from_a_previous_monitor_process(self) -> None:
        event = parse_codex_health_line(
            "app_server_connection.state_changed hostId=local next=connected previous=connecting",
            was_reconnecting=False,
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.status, "connected")

    def test_detects_reconnecting_from_retry_state(self) -> None:
        line = (
            "info [AppServerConnection] app_server_connection.state_changed "
            "cause=transport_close connectionError=NetworkError currentState=connected "
            "next=connecting previous=connected reconnectAttempt=1 reconnectTimerScheduled=true"
        )

        event = parse_codex_health_line(line, was_reconnecting=False)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.status, "reconnecting")
        self.assertIn("reconnectAttempt=1", event.detail)

    def test_detects_recovery_after_reconnect(self) -> None:
        line = (
            "info [AppServerConnection] app_server_connection.state_changed "
            "cause=post_initialize_connection_state connectionError=null "
            "next=connected previous=connecting reconnectAttempt=1"
        )

        event = parse_codex_health_line(line, was_reconnecting=True)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.status, "connected")

    def test_ignores_normal_startup_connecting_state(self) -> None:
        line = (
            "info [AppServerConnection] app_server_connection.state_changed "
            "cause=start_process connectionError=null next=connecting "
            "previous=disconnected reconnectAttempt=0 reconnectTimerScheduled=false"
        )

        self.assertIsNone(parse_codex_health_line(line, was_reconnecting=False))

    def test_ignores_cloud_and_remote_connection_failures(self) -> None:
        for host_id in ("durable", "remote-machine"):
            with self.subTest(host_id=host_id):
                line = (
                    "info [AppServerConnection] app_server_connection.state_changed "
                    f"hostId={host_id} cause=start_process connectionError=SignInRequired "
                    "next=connecting previous=error reconnectAttempt=4241"
                )
                self.assertIsNone(parse_codex_health_line(line, was_reconnecting=False))

    def test_local_connection_failure_still_triggers_waiting(self) -> None:
        line = (
            "info [AppServerConnection] app_server_connection.state_changed "
            "hostId=local cause=transport_close connectionError=NetworkError "
            "next=connecting previous=connected reconnectAttempt=1"
        )
        event = parse_codex_health_line(line, was_reconnecting=False)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.status, "reconnecting")

    def test_cloud_recovery_does_not_clear_local_failure(self) -> None:
        line = (
            "info [AppServerConnection] app_server_connection.state_changed "
            "hostId=durable cause=post_initialize_connection_state connectionError=null "
            "next=connected previous=connecting reconnectAttempt=1"
        )
        self.assertIsNone(parse_codex_health_line(line, was_reconnecting=True))


if __name__ == "__main__":
    unittest.main()
