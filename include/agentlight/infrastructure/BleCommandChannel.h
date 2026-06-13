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

#include "agentlight/infrastructure/BleConnectionLifecycle.h"

class BLE2902;
class BLEAdvertising;
class BLECharacteristic;
class BLEHIDDevice;
class BLEServer;
class BLESecurity;
class BLESecurityCallbacks;

namespace agentlight {

enum class BleConnectionState {
  Connected,
  Disconnected,
};

struct BleSecurityConfig {
  bool requirePairing;
  uint32_t pairingPin;
};

struct BleAdvertisementConfig {
  const char* advertisedName;
  const char* advertisedServiceUuid;
  uint16_t appearance;
  BleConnectionLifecycleConfig lifecycle;
};

struct BleHidProfileConfig {
  bool enabled;
  const char* manufacturerName;
  const char* modelNumber;
  uint8_t batteryLevel;
  uint16_t vendorId;
  uint16_t productId;
  uint16_t productVersion;
};

struct BleCommandChannelConfig {
  const char* deviceName;
  const char* serviceUuid;
  const char* rxUuid;
  const char* txUuid;
  BleSecurityConfig security;
  BleAdvertisementConfig advertisement;
  BleHidProfileConfig hidProfile;
};

class BleCommandChannel {
 public:
  void begin(
      const BleCommandChannelConfig& config,
      String (*handler)(const String& command),
      void (*connectionHandler)(BleConnectionState state) = nullptr);
  void openManualReconnectWindow(uint32_t nowMs);
  void closeManualReconnectWindow();
  void suspend();
  void poll(uint32_t nowMs);
  void publish(const String& message);
  bool connected() const;
  bool acceptsCommands() const;

 private:
  class ServerCallbacks;
  friend class ServerCallbacks;

  void applySecurity(const BleSecurityConfig& securityConfig);
  void applyAccessPermissions(
      BLECharacteristic* rxCharacteristic,
      BLECharacteristic* txCharacteristic,
      BLECharacteristic* hidFeatureReport,
      BLE2902* clientConfigDescriptor,
      const BleSecurityConfig& securityConfig);
  void configureHidProfile(
      BLEServer* server,
      const BleHidProfileConfig& config,
      String (*handler)(const String& command));
  void configureAdvertising(BLEAdvertising* advertising, const BleCommandChannelConfig& config);
  void handleConnected(uint16_t connectionId);
  void handleDisconnected();
  void applyAdvertisingAction(BleAdvertisingAction action);
  void notifyConnectionState(BleConnectionState state);
  void disconnectClient();

  BLECharacteristic* txCharacteristic_ = nullptr;
  BLECharacteristic* hidFeatureReport_ = nullptr;
  BLEServer* server_ = nullptr;
  BLEHIDDevice* systemHidDevice_ = nullptr;
  BLESecurity* security_ = nullptr;
  BLESecurityCallbacks* securityCallbacks_ = nullptr;
  BleConnectionLifecycle lifecycle_;
  void (*connectionHandler_)(BleConnectionState state) = nullptr;
  bool connected_ = false;
  bool commandsEnabled_ = false;
  uint16_t connectionId_ = 0;
};

}  // namespace agentlight
