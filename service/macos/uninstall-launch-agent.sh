#!/usr/bin/env bash
#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight
#

set -euo pipefail

label="com.whalesky-labs.AgentLight.agent"
plist_path="${HOME}/Library/LaunchAgents/${label}.plist"

if [[ -f "$plist_path" ]]; then
  launchctl unload "$plist_path" >/dev/null 2>&1 || true
  rm -f "$plist_path"
  printf 'Uninstalled %s\n' "$label"
else
  printf '%s is not installed.\n' "$label"
fi
