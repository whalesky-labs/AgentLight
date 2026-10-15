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
import runpy
import subprocess
import sys
import tempfile
import types
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from agentlight_agent.application.runtime_service import RuntimeService
from agentlight_agent.infrastructure.event_dispatcher import LatestEventDispatcher
from agentlight_agent.infrastructure.json_config import load_agent_config


class ServiceRuntimeTest(unittest.TestCase):
    def test_runtime_passes_its_interpreter_to_shell_children(self):
        with tempfile.TemporaryDirectory() as td:
            config = load_agent_config(Path("config/agentlight-agent.example.json"))
            config = replace(config, send_to_hardware=False, log_file=str(Path(td) / "agent.log"))
            process = Mock()
            process.wait.return_value = 0
            with patch("agentlight_agent.application.runtime_service.subprocess.Popen", return_value=process) as popen:
                RuntimeService(Path.cwd()).run_agent(Path(td) / "config.json", config,
                                                    once=True, platform_override="")
            env = popen.call_args.kwargs["env"]
            self.assertEqual(env["AGENTLIGHT_PYTHON"], Path(sys.executable).as_posix())
            self.assertEqual(env["PATH"].split(os.pathsep)[0], str(Path(sys.executable).parent))

    def test_windows_dispatch_runs_shell_entrypoint_through_configured_bash(self):
        with patch("agentlight_agent.infrastructure.commands.IS_WINDOWS", True), \
             patch.dict(os.environ, {"AGENTLIGHT_BASH": "bash"}):
            output = LatestEventDispatcher._run_command(
                [str(Path("scripts/agentlight-event").resolve()), "--agent", "codex", "--event", "tool"]
            )
        self.assertIn("agent=codex event=tool", output)
        self.assertIn("sent=false", output)


class WindowsServiceTest(unittest.TestCase):
    def setUp(self):
        class Framework:
            def __init__(self, args):
                self.statuses = []

            def ReportServiceStatus(self, status):
                self.statuses.append(status)

        self.options = {"RepoRoot": str(Path.cwd()), "PythonPath": sys.executable,
                        "UserProfile": "C:/Users/agent-owner", "ConfigPath": "C:/ProgramData/agent.json"}
        self.util = types.ModuleType("win32serviceutil")
        self.util.ServiceFramework = Framework
        self.util.GetServiceCustomOption = Mock(side_effect=lambda service, name: self.options[name])
        self.util.SetServiceCustomOption = Mock()
        self.util.HandleCommandLine = Mock(return_value=0)
        self.manager = types.ModuleType("servicemanager")
        self.manager.Initialize = Mock()
        self.manager.PrepareToHostSingle = Mock()
        self.manager.StartServiceCtrlDispatcher = Mock()
        self.modules = {"win32serviceutil": self.util,
                        "win32service": types.SimpleNamespace(SERVICE_STOP_PENDING=3),
                        "servicemanager": self.manager}
        with patch.dict(sys.modules, self.modules):
            self.module = runpy.run_path("service/windows/agentlight_service.py")
        self.cls = self.module["AgentLightWindowsService"]

    def test_host_enters_the_scm_dispatcher(self):
        with patch.dict(sys.modules, self.modules), \
             patch.object(sys, "argv", ["service.py", "--service-name", "custom-agent", "--host"]):
            self.assertEqual(self.module["main"](), 0)
        self.manager.Initialize.assert_called_once()
        self.manager.PrepareToHostSingle.assert_called_once_with(self.cls)
        self.manager.StartServiceCtrlDispatcher.assert_called_once()
        self.assertEqual(self.cls._svc_name_, "custom-agent")

    def test_install_registers_the_venv_python_with_explicit_host_mode(self):
        with patch.object(sys, "argv", ["service.py", "--service-name", "custom-agent", "install"]):
            self.module["main"]()
        self.assertEqual(self.cls._exe_name_, sys.executable)
        self.assertIn("--host", self.cls._exe_args_)
        self.assertIn("custom-agent", self.cls._exe_args_)
        self.util.HandleCommandLine.assert_called_once()

    def test_stop_kills_the_agent_process_tree_and_preserves_the_session_owner(self):
        service = self.cls(["custom-agent"])
        process = Mock(pid=123, returncode=0)
        process.poll.return_value = None

        def stop(_):
            service.SvcStop()
            return True

        with patch.object(service._stop, "wait", side_effect=stop), \
             patch("subprocess.Popen", return_value=process) as popen, \
             patch("subprocess.run", return_value=Mock(returncode=0)) as run:
            service.SvcDoRun()
        self.assertEqual(service.statuses, [3])
        command = popen.call_args.args[0]
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(popen.call_args.kwargs["env"]["USERPROFILE"], self.options["UserProfile"])
        self.assertEqual(run.call_args.args[0][-4:], ["/PID", "123", "/T", "/F"])
        process.wait.assert_called_once()

    def test_stop_before_start_does_not_launch_an_orphan_agent(self):
        service = self.cls(["custom-agent"])
        service.SvcStop()
        with patch("subprocess.Popen") as popen:
            service.SvcDoRun()
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
