#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from agentlight_agent.infrastructure.json_config import load_monitors
from agentlight_agent.infrastructure.monitor_runner import MonitorRunner


def record(kind, timestamp="2026-10-15T00:00:00Z", **fields):
    return json.dumps({"timestamp": timestamp, "type": "response_item",
                       "payload": {"type": kind, **fields}}) + "\n"


class Emitter:
    def __init__(self):
        self.events = []

    def emit_latest(self, agent, event, source, **kwargs):
        self.events.append(event)

    def close(self):
        pass


class MonitorRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.monitor = next(m for m in load_monitors(Path("config/agent-monitors.example.json"))
                            if m.name == "codex-session-jsonl")
        self.monitor = replace(self.monitor, glob=str(self.root / "*.jsonl"))
        self.emitter = Emitter()
        self.runner = MonitorRunner(self.emitter)

    def test_restart_restores_an_accepted_question_without_replaying_history(self):
        path = self.root / "pending.jsonl"
        path.write_text(record("reasoning") +
                        record("function_call", name="request_user_input_async", call_id="call_pending") +
                        record("function_call_output", call_id="call_pending", output='{"accepted":true}'))
        offsets, count = self.runner._restore_file_monitors([self.monitor], send=False)
        self.assertEqual(self.emitter.events, ["waiting"])
        self.assertEqual(count, 1)
        self.assertEqual(offsets[path], path.stat().st_size)

    def test_answered_and_failed_questions_do_not_reappear_on_restart(self):
        path = self.root / "answered.jsonl"
        path.write_text(record("function_call", name="request_user_input_async", call_id="call_failed") +
                        record("function_call_output", call_id="call_failed", output="failed to parse arguments") +
                        record("function_call", name="request_user_input_async", call_id="call_shown") +
                        record("function_call_output", call_id="call_shown", output='{"accepted":true}') +
                        record("message", role="user", content=[{"text":
                            '<send_user_message_question_reply>call_shown</send_user_message_question_reply>'}]) +
                        record("reasoning", timestamp="2026-10-15T00:01:00Z"))
        self.runner._restore_file_monitors([self.monitor], send=False)
        self.assertEqual(self.emitter.events, ["thinking"])
        self.assertFalse(self.runner._codex_inputs.has_pending)

    def test_new_file_first_question_is_not_skipped(self):
        created = False

        def advance(_):
            nonlocal created
            self.assertFalse(created)
            created = True
            (self.root / "new.jsonl").write_text(
                record("function_call", name="request_user_input_async", call_id="call_new"))
            return False

        with patch.object(self.runner._stop, "wait", side_effect=advance), contextlib.redirect_stdout(io.StringIO()):
            self.runner._run_file_monitors([self.monitor], send=False, poll_interval=.01, limit=1)
        self.assertEqual(self.emitter.events, ["waiting"])

    def test_partial_record_is_processed_after_its_newline_arrives(self):
        path = self.root / "partial.jsonl"
        line = record("function_call", name="request_user_input_async", call_id="call_partial")
        path.write_text(line[:35])
        steps = iter([line[35:]])

        def advance(_):
            with path.open("a") as file:
                file.write(next(steps))
            return False

        with patch.object(self.runner._stop, "wait", side_effect=advance), contextlib.redirect_stdout(io.StringIO()):
            self.runner._run_file_monitors([self.monitor], send=False, poll_interval=.01, limit=1)
        self.assertEqual(self.emitter.events, ["waiting"])

    def test_exited_command_monitor_is_restarted_and_its_child_is_reaped(self):
        marker = self.root / "starts"
        script = ("from pathlib import Path; "
                  f"p=Path({str(marker)!r}); p.open('a').write('started\\n')")
        health = replace(self.monitor, name="health", command=(sys.executable, "-c", script))
        thread = threading.Thread(target=self.runner._run_command_monitor,
                                  args=(health,), kwargs={"send": False, "limit": 0, "latest": True})
        thread.start()
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() or len(marker.read_text().splitlines()) < 2:
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.02)
        finally:
            self.runner._stop.set()
            thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertFalse(self.runner._processes)

    def test_health_monitor_bootstraps_a_preexisting_recovery(self):
        log = self.root / "health.log"
        log.write_text("app_server_connection.state_changed hostId=local next=connected previous=connecting\n")
        result = subprocess.run([sys.executable, "scripts/codex-health-monitor", "--glob", str(log), "--limit", "1"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("health-recovered", result.stdout)

    def test_health_monitor_waits_for_logs_created_after_startup(self):
        process = subprocess.Popen(
            [sys.executable, "scripts/codex-health-monitor", "--glob", str(self.root / "*.log"),
             "--limit", "1", "--poll-interval", ".02"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            self.assertIn("monitor started", process.stdout.readline())
            (self.root / "new.log").write_text(
                "app_server_connection.state_changed hostId=local next=connected previous=connecting\n")
            output, error = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, error)
            self.assertIn("health-recovered", output)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()

    def test_standalone_session_monitor_restores_the_same_pending_question(self):
        path = self.root / "standalone.jsonl"
        path.write_text(record("function_call", name="request_user_input_async", call_id="call_pending") +
                        record("function_call_output", call_id="call_pending", output='{"accepted":true}'))
        result = subprocess.run([sys.executable, "scripts/codex-session-monitor", "--path", str(path),
                                 "--limit", "1"], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("status="), 1)
        self.assertIn("status=waiting", result.stdout)

    @unittest.skipUnless(os.name == "posix", "Requires POSIX process signals")
    def test_agent_stop_reaps_monitor_and_command_children(self):
        marker = self.root / "child.pid"
        monitors = self.root / "monitors.json"
        monitors.write_text(json.dumps({"monitors": [
            {"name": "files", "agent": "codex", "type": "file", "format": "text",
             "glob": str(self.root / "*.jsonl"), "rules": [{"contains": "DONE", "event": "done"}]},
            {"name": "child", "agent": "codex", "type": "command", "format": "text",
             "command": [sys.executable, "-c", "import os,time; from pathlib import Path; "
                         f"Path({str(marker)!r}).write_text(str(os.getpid())); time.sleep(30)"],
             "rules": [{"contains": "READY", "event": "tool"}]},
        ]}))
        config = json.loads(Path("config/agentlight-agent.example.json").read_text())
        config.update(monitorConfig=str(monitors), sendToHardware=False, logFile=str(self.root / "agent.log"))
        config_path = self.root / "config.json"
        config_path.write_text(json.dumps(config))
        process = subprocess.Popen([sys.executable, "scripts/agentlight-agent", "--config", str(config_path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not marker.exists():
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.02)
            child_pid = int(marker.read_text())
            process.terminate()
            _, error = process.communicate(timeout=8)
            self.assertEqual(process.returncode, 0, error)
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()


if __name__ == "__main__":
    unittest.main()
