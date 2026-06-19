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
import shutil
import sys
from pathlib import Path

from agentlight_wechat.application.service import WeChatService
from agentlight_wechat.infrastructure.config_loader import load_wechat_config
from agentlight_wechat.infrastructure.paths import default_config_path, resolve_path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "wechat-agentlight.example.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AgentLight WeChat message indicator.")
    parser.add_argument(
        "command",
        choices=["run", "once", "doctor", "check-config", "print-runtime", "install-config"],
        nargs="?",
        default="run",
    )
    parser.add_argument("--config", default=os.environ.get("AGENTLIGHT_WECHAT_CONFIG", ""))
    parser.add_argument("--user-config", default=str(default_config_path()))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        if args.command == "install-config":
            source = resolve_path(args.config, Path.cwd()) if args.config else DEFAULT_CONFIG
            return _install_config(source, resolve_path(args.user_config, Path.cwd()))

        config_path = _runtime_config_path(args.config, args.user_config)
        config = load_wechat_config(config_path)
        service = WeChatService(REPO_ROOT, config_path, config)

        if args.command == "check-config":
            for line in service.check_config():
                print(line)
            return 0
        if args.command == "print-runtime":
            print(json.dumps(service.runtime_info(), ensure_ascii=False, indent=2))
            return 0
        if args.command == "doctor":
            for line in service.doctor():
                print(line)
            return 0
        if args.command == "once":
            return service.run_once()
        return service.run_forever()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _install_config(source: Path, target: Path) -> int:
    if not source.exists():
        print(f"WeChat config template not found: {source}", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(source, target)
    print(f"Config: {target}")
    return 0


def _runtime_config_path(config: str, user_config: str) -> Path:
    if config:
        return resolve_path(config, Path.cwd())

    user_path = resolve_path(user_config, Path.cwd())
    if user_path.exists():
        return user_path

    return DEFAULT_CONFIG


if __name__ == "__main__":
    raise SystemExit(main())
