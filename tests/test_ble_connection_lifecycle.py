#
# This file is part of AgentLight.
#
# @link     https://github.com/whalesky-labs/AgentLight
# @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
# @contact  root@imoi.cn
# @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


class BleConnectionLifecycleArchitectureTest(unittest.TestCase):
    def test_ble_lifecycle_state_machine_behavior(self) -> None:
        test_source = r'''
#include <cassert>
#include <cstdint>

#include "agentlight/infrastructure/BleConnectionLifecycle.h"

int main() {
  agentlight::BleConnectionLifecycle lifecycle;
  lifecycle.begin({true, 60000});

  assert(!lifecycle.connected());
  assert(!lifecycle.manualReconnectWindowOpen());
  assert(lifecycle.handleConnected() == agentlight::BleAdvertisingAction::None);
  assert(lifecycle.connected());

  assert(lifecycle.handleDisconnected(1000) == agentlight::BleAdvertisingAction::StopAdvertising);
  assert(!lifecycle.connected());
  assert(!lifecycle.manualReconnectWindowOpen());
  assert(lifecycle.poll(120000) == agentlight::BleAdvertisingAction::None);

  assert(lifecycle.openManualReconnectWindow(2000) == agentlight::BleAdvertisingAction::StartAdvertising);
  assert(lifecycle.manualReconnectWindowOpen());
  assert(lifecycle.closeManualReconnectWindow() == agentlight::BleAdvertisingAction::StopAdvertising);
  assert(!lifecycle.manualReconnectWindowOpen());
  assert(lifecycle.openManualReconnectWindow(2000) == agentlight::BleAdvertisingAction::StartAdvertising);
  assert(lifecycle.poll(61999) == agentlight::BleAdvertisingAction::None);
  assert(lifecycle.manualReconnectWindowOpen());
  assert(lifecycle.poll(62000) == agentlight::BleAdvertisingAction::StopAdvertising);
  assert(!lifecycle.manualReconnectWindowOpen());
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_path = tmp_path / "ble_lifecycle_test.cpp"
            binary_path = tmp_path / "ble_lifecycle_test"
            source_path.write_text(test_source, encoding="utf-8")

            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Iinclude",
                    str(source_path),
                    "src/infrastructure/BleConnectionLifecycle.cpp",
                    "-o",
                    str(binary_path),
                ],
                check=True,
            )
            subprocess.run([str(binary_path)], check=True)

    def test_ble_lifecycle_is_a_dedicated_state_machine(self) -> None:
        header = read("include/agentlight/infrastructure/BleConnectionLifecycle.h")
        source = read("src/infrastructure/BleConnectionLifecycle.cpp")

        self.assertIn("class BleConnectionLifecycle", header)
        self.assertIn("BleAdvertisingAction handleDisconnected", header)
        self.assertIn("BleAdvertisingAction openManualReconnectWindow", header)
        self.assertIn("BleAdvertisingAction closeManualReconnectWindow", header)
        self.assertIn("BleAdvertisingAction::StopAdvertising", source)
        self.assertIn("BleAdvertisingAction::StartAdvertising", source)

    def test_ble_channel_delegates_reconnect_policy_to_lifecycle(self) -> None:
        header = read("include/agentlight/infrastructure/BleCommandChannel.h")
        source = read("src/infrastructure/BleCommandChannel.cpp")

        self.assertIn("BleConnectionLifecycle lifecycle_", header)
        self.assertIn("lifecycle_.handleDisconnected(millis())", source)
        self.assertIn("lifecycle_.openManualReconnectWindow(nowMs)", source)
        self.assertIn("lifecycle_.closeManualReconnectWindow()", source)
        self.assertIn("lifecycle_.poll(nowMs)", source)
        self.assertNotIn(
            "AGENTLIGHT_BLE_RESTART_ADVERTISING_ON_DISCONNECT",
            read("src/main.cpp"),
        )

    def test_ble_manual_reconnect_defaults_are_explicit(self) -> None:
        platformio = read("platformio.ini")
        main = read("src/main.cpp")

        self.assertIn("AGENTLIGHT_BLE_MANUAL_RECONNECT_ADVERTISING=1", platformio)
        self.assertIn("AGENTLIGHT_BLE_MANUAL_RECONNECT_DELAY_MS=60000", platformio)
        self.assertIn("AGENTLIGHT_BLE_MANUAL_RECONNECT_BUTTON_PIN=9", platformio)
        self.assertIn("AGENTLIGHT_BLE_MANUAL_RECONNECT_BUTTON_HOLD_MS=2000", platformio)
        self.assertIn("AGENTLIGHT_BLE_MANUAL_RECONNECT_ADVERTISING", main)
        self.assertIn("AGENTLIGHT_BLE_MANUAL_RECONNECT_DELAY_MS", main)
        self.assertIn("ButtonHoldInput bleReconnectButton", main)
        self.assertIn("TransportModeController transportModeController", main)
        self.assertIn("transportModeController.update(usbChannel.hostConnected())", main)
        self.assertIn("transportModeController.bluetoothActive()", main)

    def test_transport_mode_controller_prefers_usb_host_connection(self) -> None:
        test_source = r'''
#include <cassert>

#include "agentlight/application/TransportModeController.h"

int main() {
  agentlight::TransportModeController controller;

  assert(controller.begin(true) == agentlight::TransportModeAction::EnterUsb);
  assert(controller.usbActive());
  assert(!controller.bluetoothActive());
  assert(controller.update(true) == agentlight::TransportModeAction::None);
  assert(controller.update(false) == agentlight::TransportModeAction::EnterBluetooth);
  assert(!controller.usbActive());
  assert(controller.bluetoothActive());
  assert(controller.update(false) == agentlight::TransportModeAction::None);
  assert(controller.update(true) == agentlight::TransportModeAction::EnterUsb);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_path = tmp_path / "transport_mode_test.cpp"
            binary_path = tmp_path / "transport_mode_test"
            source_path.write_text(test_source, encoding="utf-8")

            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Iinclude",
                    str(source_path),
                    "src/application/TransportModeController.cpp",
                    "-o",
                    str(binary_path),
                ],
                check=True,
            )
            subprocess.run([str(binary_path)], check=True)


if __name__ == "__main__":
    unittest.main()
