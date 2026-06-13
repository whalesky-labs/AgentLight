#!/usr/bin/env bash
#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
app_dir="${repo_root}/dist/macos/AgentLightBluetoothHelper.app"
contents_dir="${app_dir}/Contents"
macos_dir="${contents_dir}/MacOS"

rm -rf "$app_dir"
mkdir -p "$macos_dir"

swiftc \
  -O \
  -framework Foundation \
  -framework IOKit \
  "${script_dir}/AgentLightBluetoothHelper.swift" \
  -o "${macos_dir}/AgentLightBluetoothHelper"

cp "${script_dir}/AgentLightBluetoothHelper-Info.plist" "${contents_dir}/Info.plist"
chmod +x "${macos_dir}/AgentLightBluetoothHelper"

printf '%s\n' "$app_dir"
