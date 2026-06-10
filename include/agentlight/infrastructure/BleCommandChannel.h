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

class BLE2902;
class BLEAdvertising;
class BLECharacteristic;
class BLEHIDDevice;
class BLEServer;
class BLESecurity;
class BLESecurityCallbacks;

namespace agentlight {

struct BleSecurityConfig {
  bool requirePairing;
  uint32_t pairingPin;
};

struct BleSystemProfileConfig {
  bool enableHidPairingShell;
  const char* manufacturerName;
  const char* modelNumber;
  uint8_t batteryLevel;
  uint16_t vendorId;
  uint16_t productId;
  uint16_t productVersion;
};

struct BleCommandChannelConfig {
  const char* deviceName;
  const char* advertisedName;
  const char* serviceUuid;
  const char* rxUuid;
  const char* txUuid;
  uint16_t appearance;
  BleSecurityConfig security;
  BleSystemProfileConfig systemProfile;
};

class BleCommandChannel {
 public:
  void begin(const BleCommandChannelConfig& config, String (*handler)(const String& command));
  void publish(const String& message);

 private:
  void applySecurity(const BleSecurityConfig& securityConfig);
  void applyAccessPermissions(
      BLECharacteristic* rxCharacteristic,
      BLECharacteristic* txCharacteristic,
      BLE2902* clientConfigDescriptor,
      const BleSecurityConfig& securityConfig);
  void configureSystemProfile(BLEServer* server, const BleSystemProfileConfig& config);
  void configureAdvertising(BLEAdvertising* advertising, const BleCommandChannelConfig& config);

  BLECharacteristic* txCharacteristic_ = nullptr;
  BLEHIDDevice* systemHidDevice_ = nullptr;
  BLESecurity* security_ = nullptr;
  BLESecurityCallbacks* securityCallbacks_ = nullptr;
};

}  // namespace agentlight
