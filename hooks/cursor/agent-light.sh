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

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
event="${1:-}"

if [[ -z "$event" ]]; then
  event="${AGENTLIGHT_EVENT:-}"
fi

if [[ -z "$event" ]]; then
  printf 'Usage: hooks/cursor/agent-light.sh <event>\n' >&2
  exit 2
fi

"${repo_root}/scripts/agentlight-event" --agent cursor --event "$event" --send
