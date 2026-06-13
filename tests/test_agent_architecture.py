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
import tempfile
import unittest
from pathlib import Path

from agentlight_agent.application.config_service import PlatformService
from agentlight_agent.application.monitor_service import MonitorService
from agentlight_agent.application.runtime_service import RuntimeService
from agentlight_agent.domain.matching import match_event
from agentlight_agent.domain.models import MonitorFormat, MultiSessionMode
from agentlight_agent.infrastructure.json_config import load_agent_config, load_monitors, save_agent_config
from agentlight_agent.infrastructure.monitor_runner import EventEmitter


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def monitor_config(path: Path) -> Path:
    write_json(
        path,
        {
            "monitors": [
                {
                    "name": "codex-jsonl",
                    "agent": "codex",
                    "type": "file",
                    "glob": "/tmp/codex.jsonl",
                    "format": "jsonl",
                    "from_start": True,
                    "rules": [
                        {"json_path": "payload.type", "equals": "task_complete", "event": "done"},
                        {"json_path": "payload.type", "equals": "reasoning", "event": "thinking"},
                    ],
                },
                {
                    "name": "gemini-log",
                    "agent": "gemini",
                    "type": "file",
                    "glob": "/tmp/gemini.log",
                    "format": "text",
                    "rules": [{"contains": "DONE", "event": "done"}],
                },
            ]
        },
    )
    return path


def agent_config(path: Path, monitors: Path) -> Path:
    write_json(
        path,
        {
            "agentName": "whalesky-labs-AgentLight",
            "activePlatform": "codex",
            "multiSessionMode": "latest-event-wins",
            "monitorConfig": str(monitors),
            "sendToHardware": True,
            "pollIntervalSeconds": 0.1,
            "restartDelaySeconds": 3,
            "logFile": "",
            "environment": {"AGENTLIGHT_HOST": "192.168.4.1"},
        },
    )
    return path


class AgentArchitectureTest(unittest.TestCase):
    def test_load_agent_config_maps_json_to_typed_domain_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            monitors = monitor_config(tmp_path / "monitors.json")
            config = load_agent_config(agent_config(tmp_path / "agent.json", monitors))

            self.assertEqual(config.agent_name, "whalesky-labs-AgentLight")
            self.assertEqual(config.active_platform, "codex")
            self.assertEqual(config.multi_session_mode, MultiSessionMode.LATEST_EVENT_WINS)
            self.assertEqual(config.environment, {"AGENTLIGHT_HOST": "192.168.4.1"})

    def test_load_agent_config_rejects_string_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            monitors = monitor_config(tmp_path / "monitors.json")
            config_path = agent_config(tmp_path / "agent.json", monitors)
            data = json.loads(config_path.read_text(encoding="utf-8"))
            data["sendToHardware"] = "false"
            write_json(config_path, data)

            with self.assertRaisesRegex(ValueError, "sendToHardware must be a boolean"):
                load_agent_config(config_path)

    def test_load_monitors_validates_and_maps_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            monitors = load_monitors(monitor_config(tmp_path / "monitors.json"))

            self.assertEqual(len(monitors), 2)
            self.assertEqual(monitors[0].format, MonitorFormat.JSONL)
            self.assertEqual(match_event('{"payload":{"type":"task_complete"}}', monitors[0]), "done")
            self.assertEqual(match_event("status DONE", monitors[1]), "done")

    def test_platform_service_lists_and_updates_active_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            monitor_path = monitor_config(tmp_path / "monitors.json")
            config_path = agent_config(tmp_path / "agent.json", monitor_path)
            config = load_agent_config(config_path)
            monitors = load_monitors(monitor_path)

            service = PlatformService(config_path, config, monitors)

            self.assertEqual(service.configured_platforms(), ["codex", "gemini"])
            self.assertEqual(service.set_active_platform("gemini"), "gemini")
            self.assertEqual(load_agent_config(config_path).active_platform, "gemini")

    def test_monitor_service_filters_by_active_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            monitors = load_monitors(monitor_config(tmp_path / "monitors.json"))

            selected = MonitorService.filter_by_platform(monitors, "codex")

            self.assertEqual([monitor.name for monitor in selected], ["codex-jsonl"])

    def test_event_emitter_accepts_absolute_command_path(self) -> None:
        command = Path("/tmp/agentlight-event")

        emitter = EventEmitter(command)

        self.assertEqual(emitter.event_command, str(command))

    def test_runtime_info_does_not_expose_local_bluetooth_control_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            monitor_path = monitor_config(tmp_path / "monitors.json")
            config_path = agent_config(tmp_path / "agent.json", monitor_path)
            config = load_agent_config(config_path)

            info = RuntimeService(Path.cwd()).runtime_info(config_path, config)

            self.assertNotIn("controlPanel", info)

    def test_save_agent_config_does_not_write_control_server_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            monitor_path = monitor_config(tmp_path / "monitors.json")
            config_path = agent_config(tmp_path / "agent.json", monitor_path)
            config = load_agent_config(config_path)
            output_path = tmp_path / "saved.json"

            save_agent_config(output_path, config, active_platform="gemini")
            raw = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(raw["activePlatform"], "gemini")
            self.assertNotIn("controlServer", raw)
            self.assertNotIn("hardware", raw)


if __name__ == "__main__":
    unittest.main()
