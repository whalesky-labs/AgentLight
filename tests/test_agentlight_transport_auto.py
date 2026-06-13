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
import tempfile
import unittest
from pathlib import Path


class AgentLightAutoTransportTest(unittest.TestCase):
    def test_auto_transport_uses_ble_when_usb_port_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            helper = tmp_path / "AgentLightBluetoothHelper"
            helper.write_text("#!/usr/bin/env bash\nprintf 'HELPER %s\\n' \"$1\"\n", encoding="utf-8")
            helper.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "AGENTLIGHT_TRANSPORT": "auto",
                    "AGENTLIGHT_SERIAL_PORT": str(tmp_path / "missing-usb-port"),
                    "AGENTLIGHT_BLE_HELPER": str(helper),
                }
            )

            result = subprocess.run(
                ["scripts/agentlight", "status"],
                check=True,
                cwd=Path.cwd(),
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.stdout.strip(), "HELPER STATUS")


if __name__ == "__main__":
    unittest.main()
