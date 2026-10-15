#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


class EventGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.state.mkdir()
        self.gate = self.root / "agentlight-gate"
        shutil.copy2(Path(__file__).resolve().parents[1] / "scripts/agentlight-gate", self.gate)
        self.hardware = self.root / "agentlight"
        self.hardware.write_text('#!/bin/sh\nprintf "OK %s\\n" "$1"\n', encoding="utf-8")
        self.hardware.chmod(0o755)
        self.env = {
            **os.environ,
            "AGENTLIGHT_STATE_DIR": str(self.state),
            "AGENTLIGHT_GATE_LOCK_HELPER": str(Path(__file__).resolve().parents[1] /
                                               "agentlight_agent/infrastructure/process_lock.py"),
        }

    def run_gate(self, event: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(self.gate), event], env=self.env, capture_output=True, text=True, timeout=5,
        )

    def test_failed_waiting_command_does_not_block_later_task_events(self) -> None:
        self.hardware.write_text('#!/bin/sh\nexit 1\n', encoding="utf-8")
        self.assertNotEqual(self.run_gate("health-waiting").returncode, 0)
        self.assertFalse((self.state / "health-override").exists())
        self.hardware.write_text('#!/bin/sh\nprintf "OK %s\\n" "$1"\n', encoding="utf-8")
        result = self.run_gate("tool")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "OK yellow-blink")

    def test_persisted_timestamp_is_shared_wall_clock_time(self) -> None:
        before = time.time_ns() // 1_000_000
        result = self.run_gate("tool")
        after = time.time_ns() // 1_000_000
        self.assertEqual(result.returncode, 0, result.stderr)
        timestamp = int((self.state / "last-event").read_text().strip().split("|")[2])
        self.assertGreaterEqual(timestamp, before)
        self.assertLessEqual(timestamp, after)

    def test_clock_rollback_does_not_suppress_task_events(self) -> None:
        future_ms = time.time_ns() // 1_000_000 + 60_000
        (self.state / "last-event").write_text(f"tool|yellow-blink|{future_ms}\n", encoding="utf-8")
        result = self.run_gate("tool")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "OK yellow-blink")

    def test_waiting_uses_emergency_strobe(self) -> None:
        result = self.run_gate("waiting")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "OK red-strobe")

    def test_concurrent_completion_cannot_overwrite_a_later_question(self) -> None:
        calls = self.root / "calls"
        self.hardware.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$1" >> "$MOCK_CALLS"\nprintf "OK %s\\n" "$1"\n',
            encoding="utf-8",
        )
        env = {**self.env, "MOCK_CALLS": str(calls), "AGENTLIGHT_DONE_CUE_MS": "400"}
        done = subprocess.Popen(["bash", str(self.gate), "done"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: done.kill() if done.poll() is None else None)
        deadline = time.monotonic() + 3
        while not calls.exists():
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)
        waiting = subprocess.run(["bash", str(self.gate), "waiting"], env=env,
                                 capture_output=True, text=True, timeout=5)
        done.communicate(timeout=5)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(waiting.returncode, 0, waiting.stderr)
        self.assertEqual(calls.read_text().splitlines(), ["green-blink", "green", "red-strobe"])
        self.assertTrue((self.state / "last-event").read_text().startswith("waiting|red-strobe|"))

    def test_recovery_after_restart_removes_persisted_override(self) -> None:
        from agentlight_agent.domain.codex_health import parse_codex_health_line

        self.assertEqual(self.run_gate("health-waiting").returncode, 0)
        self.assertIn("SKIP health-override", self.run_gate("waiting").stdout)
        recovered = parse_codex_health_line(
            "app_server_connection.state_changed hostId=local next=connected previous=connecting",
            was_reconnecting=False,
        )
        self.assertEqual(recovered.status, "connected")
        self.assertEqual(self.run_gate("health-recovered").stdout.strip(), "OK red-strobe")
        self.assertFalse((self.state / "health-override").exists())


if __name__ == "__main__":
    unittest.main()
