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

if [[ $# -lt 2 ]]; then
  printf 'Usage: hooks/agents/generic-wrapper.sh <agent> <command> [args...]\n' >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
agent="$1"
shift

emit_status() {
  if ! "${repo_root}/scripts/agentlight-event" --agent "$agent" --event "$1" --send; then
    printf 'AgentLight status update failed: %s\n' "$1" >&2
  fi
}

emit_status start

if "$@"; then
  emit_status done
else
  status=$?
  emit_status error
  exit "$status"
fi
