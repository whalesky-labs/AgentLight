#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  printf 'Usage: hooks/agents/generic-wrapper.sh <agent> <command> [args...]\n' >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
agent="$1"
shift

"${repo_root}/scripts/agentlight-event" --agent "$agent" --event start --send

if "$@"; then
  "${repo_root}/scripts/agentlight-event" --agent "$agent" --event done --send
else
  status=$?
  "${repo_root}/scripts/agentlight-event" --agent "$agent" --event error --send
  exit "$status"
fi
