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

