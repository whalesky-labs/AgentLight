/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include "agentlight/infrastructure/BleCommandChannel.h"

#include <BLE2902.h>
#include <BLEAdvertising.h>
#include <BLEDevice.h>
#include <BLEHIDDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

namespace agentlight {

namespace {

constexpr uint8_t BLE_KEY_SIZE = 16;
constexpr uint8_t HID_COMMAND_FEATURE_REPORT_ID = 1;
constexpr uint8_t HID_COMMAND_FEATURE_REPORT_SIZE = 32;
constexpr uint8_t HID_COMMAND_MAX_TEXT_SIZE = HID_COMMAND_FEATURE_REPORT_SIZE - 1;

uint8_t hidGenericReportMap[] = {
    0x06, 0x00, 0xFF,  // Usage Page (Vendor Defined 0xFF00)
    0x09, 0x01,        // Usage (Vendor Usage 1)
    0xA1, 0x01,        // Collection (Application)
    0x85, HID_COMMAND_FEATURE_REPORT_ID,
    0x09, 0x01,        // Usage (Vendor Usage 1)
    0x15, 0x00,        // Logical Minimum (0)
    0x26, 0xFF, 0x00,  // Logical Maximum (255)
    0x75, 0x08,        // Report Size (8)
    0x95, HID_COMMAND_FEATURE_REPORT_SIZE,
    0xB1, 0x02,        // Feature (Data, Variable, Absolute)
    0xC0,              // End Collection
};

void writeHidTextReport(BLECharacteristic* characteristic, const String& text) {
  if (characteristic == nullptr) {
    return;
  }

  uint8_t report[HID_COMMAND_FEATURE_REPORT_SIZE] = {0};
  const uint8_t textLength = static_cast<uint8_t>(
      min(text.length(), static_cast<unsigned int>(HID_COMMAND_MAX_TEXT_SIZE)));
  report[0] = textLength;

  for (uint8_t index = 0; index < textLength; ++index) {
    report[index + 1] = static_cast<uint8_t>(text.charAt(index));
  }

  characteristic->setValue(report, sizeof(report));
}

String decodeHidTextReport(const uint8_t* data, size_t length) {
  if (data == nullptr || length == 0) {
    return "";
  }

  size_t cursor = 0;
  if (length > 1 && data[0] == HID_COMMAND_FEATURE_REPORT_ID) {
    cursor = 1;
  }

  if (cursor >= length) {
    return "";
  }

  const uint8_t textLength = data[cursor];
  const size_t available = length - cursor - 1;
  if (textLength == 0 || textLength > available || textLength > HID_COMMAND_MAX_TEXT_SIZE) {
    return "";
  }

  char buffer[HID_COMMAND_MAX_TEXT_SIZE + 1] = {0};
  for (uint8_t index = 0; index < textLength; ++index) {
    buffer[index] = static_cast<char>(data[cursor + 1 + index]);
  }

  return String(buffer);
}

class RxCallbacks : public BLECharacteristicCallbacks {
 public:
  RxCallbacks(BleCommandChannel& channel, String (*handler)(const String& command))
      : channel_(channel), handler_(handler) {}

  void onWrite(BLECharacteristic* characteristic) override {
    const auto value = characteristic->getValue();
    if (value.length() == 0) {
      return;
    }

    if (!channel_.acceptsCommands()) {
      channel_.publish("SKIP BLE_SUSPENDED");
      return;
    }

    const String response = handler_(String(value.c_str()));
    channel_.publish(response);
  }

 private:
  BleCommandChannel& channel_;
  String (*handler_)(const String& command);
};

class HidCommandCallbacks : public BLECharacteristicCallbacks {
 public:
  HidCommandCallbacks(BleCommandChannel& channel, String (*handler)(const String& command))
      : channel_(channel), handler_(handler) {}

  void onWrite(BLECharacteristic* characteristic, esp_ble_gatts_cb_param_t* param) override {
    const String command = decodeHidTextReport(param->write.value, param->write.len);
    if (command.length() == 0) {
      writeHidTextReport(characteristic, "ERROR HID_EMPTY_COMMAND");
      return;
    }

    if (!channel_.acceptsCommands()) {
      writeHidTextReport(characteristic, "SKIP BLE_SUSPENDED");
      return;
    }

    const String response = handler_(command);
    writeHidTextReport(characteristic, response);
  }

 private:
  BleCommandChannel& channel_;
  String (*handler_)(const String& command);
};

class PinPairingCallbacks : public BLESecurityCallbacks {
 public:
  explicit PinPairingCallbacks(uint32_t pairingPin) : pairingPin_(pairingPin) {}

  uint32_t onPassKeyRequest() override {
    Serial.print("AgentLight BLE passkey requested: ");
    printPasskey(pairingPin_);
    return pairingPin_;
  }

  void onPassKeyNotify(uint32_t passKey) override {
    Serial.print("AgentLight BLE passkey: ");
    printPasskey(passKey);
  }

  bool onSecurityRequest() override {
    Serial.println("AgentLight BLE security request accepted");
    return true;
  }

  void onAuthenticationComplete(esp_ble_auth_cmpl_t authentication) override {
    Serial.print("AgentLight BLE pairing ");
    Serial.println(authentication.success ? "succeeded" : "failed");
  }

  bool onConfirmPIN(uint32_t pin) override {
    Serial.print("AgentLight BLE numeric confirmation: ");
    printPasskey(pin);
    return true;
  }

 private:
  void printPasskey(uint32_t passKey) {
    char buffer[7];
    snprintf(buffer, sizeof(buffer), "%06lu", static_cast<unsigned long>(passKey));
    Serial.println(buffer);
  }

  uint32_t pairingPin_;
};

}  // namespace

class BleCommandChannel::ServerCallbacks : public BLEServerCallbacks {
 public:
  ServerCallbacks(BleCommandChannel& channel, const BleSecurityConfig& securityConfig)
      : channel_(channel), securityConfig_(securityConfig) {}

  void onConnect(BLEServer* server) override {
    (void)server;
  }

  void onConnect(BLEServer* server, esp_ble_gatts_cb_param_t* param) override {
    (void)server;
    channel_.handleConnected(param->connect.conn_id);
    if (!securityConfig_.requirePairing) {
      return;
    }

    const esp_err_t result = esp_ble_set_encryption(
        param->connect.remote_bda,
        ESP_BLE_SEC_ENCRYPT_MITM);
    Serial.print("AgentLight BLE encryption requested: ");
    Serial.println(result == ESP_OK ? "OK" : "FAILED");
  }

  void onDisconnect(BLEServer* server) override {
    (void)server;
    channel_.handleDisconnected();
  }

 private:
  BleCommandChannel& channel_;
  BleSecurityConfig securityConfig_;
};

void BleCommandChannel::begin(
    const BleCommandChannelConfig& config,
    String (*handler)(const String& command),
    void (*connectionHandler)(BleConnectionState state)) {
  lifecycle_.begin(config.advertisement.lifecycle);
  connectionHandler_ = connectionHandler;

  BLEDevice::init(config.deviceName);
  applySecurity(config.security);

  server_ = BLEDevice::createServer();
  server_->setCallbacks(new ServerCallbacks(*this, config.security));

  configureHidProfile(server_, config.hidProfile, handler);

  BLEService* service = server_->createService(config.serviceUuid);

  txCharacteristic_ = service->createCharacteristic(
      config.txUuid,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  BLE2902* clientConfigDescriptor = new BLE2902();
  txCharacteristic_->addDescriptor(clientConfigDescriptor);
  txCharacteristic_->setValue("STATUS OFF");

  BLECharacteristic* rxCharacteristic = service->createCharacteristic(
      config.rxUuid,
      BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  rxCharacteristic->setCallbacks(new RxCallbacks(*this, handler));

  applyAccessPermissions(rxCharacteristic, txCharacteristic_, hidFeatureReport_, clientConfigDescriptor, config.security);

  service->start();

  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  configureAdvertising(advertising, config);
}

void BleCommandChannel::poll(uint32_t nowMs) {
  applyAdvertisingAction(lifecycle_.poll(nowMs));
}

void BleCommandChannel::openManualReconnectWindow(uint32_t nowMs) {
  commandsEnabled_ = true;
  applyAdvertisingAction(lifecycle_.openManualReconnectWindow(nowMs));
}

void BleCommandChannel::closeManualReconnectWindow() {
  applyAdvertisingAction(lifecycle_.closeManualReconnectWindow());
}

void BleCommandChannel::suspend() {
  commandsEnabled_ = false;
  closeManualReconnectWindow();
  BLEDevice::stopAdvertising();
  disconnectClient();
}

void BleCommandChannel::applySecurity(const BleSecurityConfig& securityConfig) {
  if (!securityConfig.requirePairing) {
    return;
  }

  securityCallbacks_ = new PinPairingCallbacks(securityConfig.pairingPin);
  BLEDevice::setSecurityCallbacks(securityCallbacks_);
  BLEDevice::setEncryptionLevel(ESP_BLE_SEC_ENCRYPT_MITM);

  security_ = new BLESecurity();
  security_->setStaticPIN(securityConfig.pairingPin);
  security_->setCapability(ESP_IO_CAP_OUT);
  security_->setKeySize(BLE_KEY_SIZE);
  security_->setAuthenticationMode(ESP_LE_AUTH_REQ_SC_MITM_BOND);
  security_->setInitEncryptionKey(ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK);
  security_->setRespEncryptionKey(ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK);
}

void BleCommandChannel::applyAccessPermissions(
    BLECharacteristic* rxCharacteristic,
    BLECharacteristic* txCharacteristic,
    BLECharacteristic* hidFeatureReport,
    BLE2902* clientConfigDescriptor,
    const BleSecurityConfig& securityConfig) {
  if (!securityConfig.requirePairing) {
    return;
  }

  txCharacteristic->setAccessPermissions(ESP_GATT_PERM_READ_ENC_MITM);
  rxCharacteristic->setAccessPermissions(ESP_GATT_PERM_WRITE_ENC_MITM);
  if (hidFeatureReport != nullptr) {
    hidFeatureReport->setAccessPermissions(
        ESP_GATT_PERM_READ_ENC_MITM | ESP_GATT_PERM_WRITE_ENC_MITM);
  }
  clientConfigDescriptor->setAccessPermissions(
      ESP_GATT_PERM_READ_ENC_MITM | ESP_GATT_PERM_WRITE_ENC_MITM);
}

void BleCommandChannel::configureHidProfile(
    BLEServer* server,
    const BleHidProfileConfig& config,
    String (*handler)(const String& command)) {
  if (!config.enabled) {
    return;
  }

  systemHidDevice_ = new BLEHIDDevice(server);
  systemHidDevice_->manufacturer();
  systemHidDevice_->manufacturer(config.manufacturerName);

  BLECharacteristic* modelNumber = systemHidDevice_->deviceInfo()->createCharacteristic(
      BLEUUID(static_cast<uint16_t>(0x2A24)),
      BLECharacteristic::PROPERTY_READ);
  modelNumber->setValue(config.modelNumber);

  systemHidDevice_->pnp(0x02, config.vendorId, config.productId, config.productVersion);
  systemHidDevice_->hidInfo(0x00, 0x00);
  systemHidDevice_->reportMap(hidGenericReportMap, sizeof(hidGenericReportMap));

  hidFeatureReport_ = systemHidDevice_->featureReport(HID_COMMAND_FEATURE_REPORT_ID);
  hidFeatureReport_->setCallbacks(new HidCommandCallbacks(*this, handler));
  writeHidTextReport(hidFeatureReport_, "STATUS OFF");

  systemHidDevice_->startServices();
  const uint8_t batteryLevel = config.batteryLevel > 100 ? 100 : config.batteryLevel;
  systemHidDevice_->setBatteryLevel(batteryLevel);
}

void BleCommandChannel::configureAdvertising(BLEAdvertising* advertising, const BleCommandChannelConfig& config) {
  BLEAdvertisementData advertisement;
  advertisement.setFlags(ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT);
  advertisement.setName(config.advertisement.advertisedName);
  advertisement.setCompleteServices(BLEUUID(config.advertisement.advertisedServiceUuid));
  advertisement.setAppearance(config.advertisement.appearance);

  BLEAdvertisementData scanResponse;
  scanResponse.setName(config.deviceName);

  advertising->setAdvertisementType(ADV_TYPE_IND);
  advertising->setScanResponse(true);
  advertising->setAdvertisementData(advertisement);
  advertising->setScanResponseData(scanResponse);
}

void BleCommandChannel::handleConnected(uint16_t connectionId) {
  connected_ = true;
  connectionId_ = connectionId;
  applyAdvertisingAction(lifecycle_.handleConnected());
  notifyConnectionState(BleConnectionState::Connected);
}

void BleCommandChannel::handleDisconnected() {
  connected_ = false;
  connectionId_ = 0;
  notifyConnectionState(BleConnectionState::Disconnected);
  applyAdvertisingAction(lifecycle_.handleDisconnected(millis()));
}

void BleCommandChannel::applyAdvertisingAction(BleAdvertisingAction action) {
  switch (action) {
    case BleAdvertisingAction::StartAdvertising:
      BLEDevice::startAdvertising();
      return;
    case BleAdvertisingAction::StopAdvertising:
      BLEDevice::stopAdvertising();
      return;
    case BleAdvertisingAction::None:
    default:
      return;
  }
}

void BleCommandChannel::notifyConnectionState(BleConnectionState state) {
  if (connectionHandler_ != nullptr) {
    connectionHandler_(state);
  }
}

void BleCommandChannel::disconnectClient() {
  if (!connected_ || server_ == nullptr) {
    return;
  }

  server_->disconnect(connectionId_);
}

void BleCommandChannel::publish(const String& message) {
  if (txCharacteristic_ == nullptr) {
    return;
  }

  txCharacteristic_->setValue(message.c_str());
  txCharacteristic_->notify();
}

bool BleCommandChannel::connected() const {
  return connected_;
}

bool BleCommandChannel::acceptsCommands() const {
  return commandsEnabled_;
}

}  // namespace agentlight
