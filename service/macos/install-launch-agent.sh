#!/usr/bin/env bash
set -euo pipefail

label="com.whaleskylabs.agentlight.agent"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
config_dir="${HOME}/.agentlight"
config_path="${config_dir}/agentlight-agent.json"
log_dir="${HOME}/Library/Logs/AgentLight"
plist_dir="${HOME}/Library/LaunchAgents"
plist_path="${plist_dir}/${label}.plist"
python_path="${PYTHON_PATH:-$(command -v python3)}"

mkdir -p "$config_dir" "$log_dir" "$plist_dir"

if [[ ! -f "$config_path" ]]; then
  cp "${repo_root}/config/agentlight-agent.example.json" "$config_path"
fi

cat > "$plist_path" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${python_path}</string>
    <string>${repo_root}/scripts/agentlight-agent</string>
    <string>run</string>
    <string>--config</string>
    <string>${config_path}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${repo_root}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${log_dir}/launchagent.out.log</string>
  <key>StandardErrorPath</key>
  <string>${log_dir}/launchagent.err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>AGENTLIGHT_AGENT_CONFIG</key>
    <string>${config_path}</string>
  </dict>
</dict>
</plist>
PLIST

launchctl unload "$plist_path" >/dev/null 2>&1 || true
launchctl load "$plist_path"

printf 'Installed %s\n' "$label"
printf 'Config: %s\n' "$config_path"
printf 'Logs: %s\n' "$log_dir"
