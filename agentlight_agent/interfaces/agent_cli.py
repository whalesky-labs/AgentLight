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
import json
import os
import sys
from pathlib import Path

from agentlight_agent.application.config_service import PlatformService
from agentlight_agent.application.runtime_service import RuntimeService
from agentlight_agent.infrastructure.json_config import load_agent_config, load_monitors
from agentlight_agent.infrastructure.paths import resolve_path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "agentlight-agent.example.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AgentLight background agent.")
    parser.add_argument(
        "command",
        choices=["run", "check-config", "print-runtime", "platform"],
        nargs="?",
        default="run",
    )
    parser.add_argument("platform_action", nargs="?", choices=["get", "list", "set"])
    parser.add_argument("platform_value", nargs="?")
    parser.add_argument("--config", default=os.environ.get("AGENTLIGHT_AGENT_CONFIG", str(DEFAULT_CONFIG)))
    parser.add_argument("--platform", default=os.environ.get("AGENTLIGHT_ACTIVE_PLATFORM", ""))
    parser.add_argument("--once", action="store_true", help="Run one monitor pass and exit. Intended for tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = resolve_path(args.config, Path.cwd())

    try:
        config = load_agent_config(config_path)
        runtime = RuntimeService(REPO_ROOT)

        if args.command == "check-config":
            for key, value in runtime.runtime_info(config_path, config).items():
                print(f"{key}={value}")
            return 0

        if args.command == "print-runtime":
            print(json.dumps(runtime.runtime_info(config_path, config), ensure_ascii=False, indent=2))
            return 0

        if args.command == "platform":
            monitor_config = resolve_path(config.monitor_config, REPO_ROOT)
            service = PlatformService(config_path, config, load_monitors(monitor_config))
            return _handle_platform_command(service, args.platform_action, args.platform_value)

        return runtime.run_agent(config_path, config, once=args.once, platform_override=args.platform)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _handle_platform_command(service: PlatformService, action: str | None, value: str | None) -> int:
    action = action or "get"
    if action == "get":
        print(service.active_platform())
        return 0
    if action == "list":
        active_platform = service.active_platform()
        for platform in service.configured_platforms():
            marker = "*" if platform == active_platform else " "
            print(f"{marker} {platform}")
        return 0
    if action == "set":
        print(f"activePlatform={service.set_active_platform(value or '')}")
        return 0
    raise ValueError(f"Unknown platform action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())

