#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def exclusive_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as file:
        if os.name == "nt":
            import msvcrt

            if file.seek(0, 2) == 0:
                file.write(b"\0")
                file.flush()
            file.seek(0)
            while True:
                try:
                    msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if exc.errno not in {11, 13, 36}:
                        raise
                    time.sleep(0.05)
            try:
                yield
            finally:
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(file, fcntl.LOCK_UN)


def main() -> int:
    state_dir, gate, *arguments = sys.argv[1:]
    env = {**os.environ, "AGENTLIGHT_GATE_LOCK_HELD": "1"}
    with exclusive_lock(Path(state_dir) / "gate.lock"):
        return subprocess.call([env.get("AGENTLIGHT_BASH", "bash"), gate, *arguments], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
