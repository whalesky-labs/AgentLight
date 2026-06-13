/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#pragma once

namespace agentlight {

enum class TransportMode {
  Usb,
  Bluetooth,
};

enum class TransportModeAction {
  None,
  EnterUsb,
  EnterBluetooth,
};

class TransportModeController {
 public:
  TransportModeAction begin(bool usbHostConnected);
  TransportModeAction update(bool usbHostConnected);

  TransportMode mode() const;
  bool usbActive() const;
  bool bluetoothActive() const;

 private:
  TransportMode resolve(bool usbHostConnected) const;
  TransportModeAction actionFor(TransportMode mode) const;

  bool initialized_ = false;
  TransportMode mode_ = TransportMode::Bluetooth;
};

}  // namespace agentlight
