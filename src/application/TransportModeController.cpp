/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include "agentlight/application/TransportModeController.h"

namespace agentlight {

TransportModeAction TransportModeController::begin(bool usbHostConnected) {
  initialized_ = true;
  mode_ = resolve(usbHostConnected);
  return actionFor(mode_);
}

TransportModeAction TransportModeController::update(bool usbHostConnected) {
  if (!initialized_) {
    return begin(usbHostConnected);
  }

  const TransportMode nextMode = resolve(usbHostConnected);
  if (nextMode == mode_) {
    return TransportModeAction::None;
  }

  mode_ = nextMode;
  return actionFor(mode_);
}

TransportMode TransportModeController::mode() const {
  return mode_;
}

bool TransportModeController::usbActive() const {
  return initialized_ && mode_ == TransportMode::Usb;
}

bool TransportModeController::bluetoothActive() const {
  return initialized_ && mode_ == TransportMode::Bluetooth;
}

TransportMode TransportModeController::resolve(bool usbHostConnected) const {
  return usbHostConnected ? TransportMode::Usb : TransportMode::Bluetooth;
}

TransportModeAction TransportModeController::actionFor(TransportMode mode) const {
  return mode == TransportMode::Usb
      ? TransportModeAction::EnterUsb
      : TransportModeAction::EnterBluetooth;
}

}  // namespace agentlight
