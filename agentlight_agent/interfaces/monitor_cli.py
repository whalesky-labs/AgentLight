from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentlight_agent.application.monitor_service import MonitorService
from agentlight_agent.infrastructure.json_config import load_monitors
from agentlight_agent.infrastructure.monitor_runner import EventEmitter, MonitorRunner


REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor multiple AI agent outputs and normalize status events.")
    parser.add_argument(
        "--config",
        default="config/agent-monitors.example.json",
        help="Path to monitor config JSON.",
    )
    parser.add_argument("--once", action="store_true", help="Process existing content once and exit.")
    parser.add_argument("--send", action="store_true", help="Forward normalized events to scripts/agentlight-event --send.")
    parser.add_argument("--platform", default="", help="Only run monitors for this platform/agent.")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Polling interval for file monitors.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum normalized events to print before exit.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)

    try:
        monitors = load_monitors(config_path)
        monitors = MonitorService.filter_by_platform(monitors, args.platform)
        if args.platform and not monitors:
            print(f"No monitors configured for platform: {args.platform}", file=sys.stderr)
            return 1

        service = MonitorService(MonitorRunner(EventEmitter(REPO_ROOT / "scripts" / "agentlight-event")))
        return service.run(
            monitors,
            once=args.once,
            send=args.send,
            poll_interval=args.poll_interval,
            limit=args.limit,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
