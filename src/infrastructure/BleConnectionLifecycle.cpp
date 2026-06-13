/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include "agentlight/infrastructure/BleConnectionLifecycle.h"

namespace agentlight {

void BleConnectionLifecycle::begin(const BleConnectionLifecycleConfig& config) {
  config_ = config;
  connected_ = false;
  manualReconnectWindowOpen_ = false;
  manualReconnectWindowUntilMs_ = 0;
}

BleAdvertisingAction BleConnectionLifecycle::handleConnected() {
  connected_ = true;
  manualReconnectWindowOpen_ = false;
  return BleAdvertisingAction::None;
}

BleAdvertisingAction BleConnectionLifecycle::handleDisconnected(uint32_t nowMs) {
  (void)nowMs;
  connected_ = false;
  manualReconnectWindowOpen_ = false;
  return BleAdvertisingAction::StopAdvertising;
}

BleAdvertisingAction BleConnectionLifecycle::openManualReconnectWindow(uint32_t nowMs) {
  if (!config_.manualReconnectWindowEnabled || connected_) {
    return BleAdvertisingAction::None;
  }

  manualReconnectWindowUntilMs_ = nowMs + config_.manualReconnectWindowMs;
  manualReconnectWindowOpen_ = true;
  return BleAdvertisingAction::StartAdvertising;
}

BleAdvertisingAction BleConnectionLifecycle::closeManualReconnectWindow() {
  if (!manualReconnectWindowOpen_) {
    return BleAdvertisingAction::None;
  }

  manualReconnectWindowOpen_ = false;
  return BleAdvertisingAction::StopAdvertising;
}

BleAdvertisingAction BleConnectionLifecycle::poll(uint32_t nowMs) {
  if (!manualReconnectWindowOpen_ || connected_) {
    return BleAdvertisingAction::None;
  }

  const int32_t remainingMs = static_cast<int32_t>(manualReconnectWindowUntilMs_ - nowMs);
  if (remainingMs > 0) {
    return BleAdvertisingAction::None;
  }

  manualReconnectWindowOpen_ = false;
  return BleAdvertisingAction::StopAdvertising;
}

bool BleConnectionLifecycle::connected() const {
  return connected_;
}

bool BleConnectionLifecycle::manualReconnectWindowOpen() const {
  return manualReconnectWindowOpen_;
}

}  // namespace agentlight
