/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#pragma once

#include <stdint.h>

namespace agentlight {

enum class BleAdvertisingAction {
  None,
  StartAdvertising,
  StopAdvertising,
};

struct BleConnectionLifecycleConfig {
  bool manualReconnectWindowEnabled;
  uint32_t manualReconnectWindowMs;
};

class BleConnectionLifecycle {
 public:
  void begin(const BleConnectionLifecycleConfig& config);
  BleAdvertisingAction handleConnected();
  BleAdvertisingAction handleDisconnected(uint32_t nowMs);
  BleAdvertisingAction openManualReconnectWindow(uint32_t nowMs);
  BleAdvertisingAction closeManualReconnectWindow();
  BleAdvertisingAction poll(uint32_t nowMs);

  bool connected() const;
  bool manualReconnectWindowOpen() const;

 private:
  BleConnectionLifecycleConfig config_{false, 0};
  bool connected_ = false;
  bool manualReconnectWindowOpen_ = false;
  uint32_t manualReconnectWindowUntilMs_ = 0;
};

}  // namespace agentlight
