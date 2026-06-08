#!/usr/bin/env bash
set -euo pipefail

label="com.whaleskylabs.agentlight.agent"
plist_path="${HOME}/Library/LaunchAgents/${label}.plist"

if [[ -f "$plist_path" ]]; then
  launchctl unload "$plist_path" >/dev/null 2>&1 || true
  rm -f "$plist_path"
  printf 'Uninstalled %s\n' "$label"
else
  printf '%s is not installed.\n' "$label"
fi
