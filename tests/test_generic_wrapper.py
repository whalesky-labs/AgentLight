#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class GenericWrapperTest(unittest.TestCase):
    def test_hardware_failures_do_not_skip_the_task_or_change_its_exit_status(self):
        for code in [0, 7]:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "hooks/agents").mkdir(parents=True)
                (root / "scripts").mkdir()
                wrapper = root / "hooks/agents/generic-wrapper.sh"
                shutil.copy2("hooks/agents/generic-wrapper.sh", wrapper)
                event = root / "scripts/agentlight-event"
                event.write_text("#!/bin/sh\nexit 1\n")
                event.chmod(0o755)
                marker = root / "ran"
                result = subprocess.run(["bash", str(wrapper), "codex", "bash", "-c",
                                         'touch "$1"; exit "$2"', "task", str(marker), str(code)],
                                        capture_output=True, text=True, timeout=5)
                self.assertTrue(marker.exists())
                self.assertEqual(result.returncode, code)
                self.assertIn("status update failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
