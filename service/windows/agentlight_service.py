#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
from pathlib import Path

import win32service
import win32serviceutil


class AgentLightWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = "whalesky-labs-AgentLight"
    _svc_display_name_ = "WhaleSky Labs AgentLight"
    _svc_description_ = "AI Agent status light synchronization."

    def __init__(self, args):
        super().__init__(args)
        self._service_name = args[0]
        self._stop = threading.Event()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self._stop.set()

    def SvcDoRun(self):
        option = lambda name: win32serviceutil.GetServiceCustomOption(self._service_name, name)
        repo = Path(option("RepoRoot"))
        env = os.environ.copy()
        env["USERPROFILE"] = option("UserProfile")
        env["HOME"] = env["USERPROFILE"]
        command = [option("PythonPath"), str(repo / "scripts/agentlight-agent"), "run",
                   "--config", option("ConfigPath")]
        if self._stop.is_set():
            return
        process = subprocess.Popen(command, cwd=str(repo), env=env)
        try:
            while process.poll() is None:
                if self._stop.wait(0.2):
                    taskkill = Path(env.get("SystemRoot", "C:/Windows")) / "System32/taskkill.exe"
                    result = subprocess.run([str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                                            check=False, capture_output=True)
                    if result.returncode and process.poll() is None:
                        process.terminate()
                    return
            raise RuntimeError(f"AgentLight agent exited unexpectedly: {process.returncode}")
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def install_options(options):
    names = {"--config": "ConfigPath", "--repo": "RepoRoot", "--python": "PythonPath",
             "--user-profile": "UserProfile"}
    values = dict(options)
    for name, registry_name in names.items():
        if not values.get(name):
            raise ValueError(f"Missing service installation option: {name}")
        win32serviceutil.SetServiceCustomOption(AgentLightWindowsService._svc_name_, registry_name, values[name])


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--service-name", default=AgentLightWindowsService._svc_name_)
    parser.add_argument("--display-name", default=AgentLightWindowsService._svc_display_name_)
    parser.add_argument("--host", action="store_true")
    args, remaining = parser.parse_known_args()
    AgentLightWindowsService._svc_name_ = args.service_name
    AgentLightWindowsService._svc_display_name_ = args.display_name
    if args.host:
        import servicemanager

        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AgentLightWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
        return 0
    AgentLightWindowsService._exe_name_ = sys.executable
    AgentLightWindowsService._exe_args_ = subprocess.list2cmdline(
        [str(Path(__file__).resolve()), "--service-name", args.service_name, "--host"]
    )
    return win32serviceutil.HandleCommandLine(
        AgentLightWindowsService, argv=[sys.argv[0], *remaining],
        customInstallOptions="config=repo=python=user-profile=", customOptionHandler=install_options,
    )


if __name__ == "__main__":
    raise SystemExit(main() or 0)
