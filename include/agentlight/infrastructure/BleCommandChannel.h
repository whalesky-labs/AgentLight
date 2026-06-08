/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#pragma once

#include <Arduino.h>
#include <BLECharacteristic.h>

namespace agentlight {

class BleCommandChannel {
 public:
  void begin(const char* deviceName, String (*handler)(const String& command));
  void publish(const String& message);

 private:
  BLECharacteristic* txCharacteristic_ = nullptr;
};

}  // namespace agentlight

