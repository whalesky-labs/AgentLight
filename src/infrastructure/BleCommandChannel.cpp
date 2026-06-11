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
constexpr uint8_t HID_GENERIC_FEATURE_REPORT_ID = 1;

uint8_t hidGenericReportMap[] = {
    0x06, 0x00, 0xFF,  // Usage Page (Vendor Defined 0xFF00)
    0x09, 0x01,        // Usage (Vendor Usage 1)
    0xA1, 0x01,        // Collection (Application)
    0x85, HID_GENERIC_FEATURE_REPORT_ID,
    0x09, 0x01,        // Usage (Vendor Usage 1)
    0x15, 0x00,        // Logical Minimum (0)
    0x26, 0xFF, 0x00,  // Logical Maximum (255)
    0x75, 0x08,        // Report Size (8)
    0x95, 0x01,        // Report Count (1)
    0xB1, 0x02,        // Feature (Data, Variable, Absolute)
    0xC0,              // End Collection
};

class ServerCallbacks : public BLEServerCallbacks {
 public:
  explicit ServerCallbacks(const BleSecurityConfig& securityConfig)
      : securityConfig_(securityConfig) {}

  void onConnect(BLEServer* server) override {
    (void)server;
  }

  void onConnect(BLEServer* server, esp_ble_gatts_cb_param_t* param) override {
    (void)server;
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
    server->startAdvertising();
  }

 private:
  BleSecurityConfig securityConfig_;
};

class RxCallbacks : public BLECharacteristicCallbacks {
 public:
  RxCallbacks(BleCommandChannel& channel, String (*handler)(const String& command))
      : channel_(channel), handler_(handler) {}

  void onWrite(BLECharacteristic* characteristic) override {
    const auto value = characteristic->getValue();
    if (value.length() == 0) {
      return;
    }

    const String response = handler_(String(value.c_str()));
    channel_.publish(response);
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

void BleCommandChannel::begin(const BleCommandChannelConfig& config, String (*handler)(const String& command)) {
  BLEDevice::init(config.deviceName);
  applySecurity(config.security);

  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks(config.security));

  configureSystemProfile(server, config.systemProfile);

  BLEService* service = server->createService(config.serviceUuid);

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

  applyAccessPermissions(rxCharacteristic, txCharacteristic_, clientConfigDescriptor, config.security);

  service->start();

  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  configureAdvertising(advertising, config);
  BLEDevice::startAdvertising();
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
    BLE2902* clientConfigDescriptor,
    const BleSecurityConfig& securityConfig) {
  if (!securityConfig.requirePairing) {
    return;
  }

  txCharacteristic->setAccessPermissions(ESP_GATT_PERM_READ_ENC_MITM);
  rxCharacteristic->setAccessPermissions(ESP_GATT_PERM_WRITE_ENC_MITM);
  clientConfigDescriptor->setAccessPermissions(
      ESP_GATT_PERM_READ_ENC_MITM | ESP_GATT_PERM_WRITE_ENC_MITM);
}

void BleCommandChannel::configureSystemProfile(BLEServer* server, const BleSystemProfileConfig& config) {
  if (!config.enableHidPairingShell) {
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

  BLECharacteristic* featureReport = systemHidDevice_->featureReport(HID_GENERIC_FEATURE_REPORT_ID);
  uint8_t featureValue = 0;
  featureReport->setValue(&featureValue, 1);

  systemHidDevice_->startServices();
  const uint8_t batteryLevel = config.batteryLevel > 100 ? 100 : config.batteryLevel;
  systemHidDevice_->setBatteryLevel(batteryLevel);
}

void BleCommandChannel::configureAdvertising(BLEAdvertising* advertising, const BleCommandChannelConfig& config) {
  BLEAdvertisementData advertisement;
  advertisement.setFlags(ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT);
  advertisement.setName(config.advertisedName);
  if (config.systemProfile.enableHidPairingShell) {
    advertisement.setCompleteServices(BLEUUID(static_cast<uint16_t>(0x1812)));
  } else {
    advertisement.setCompleteServices(BLEUUID(config.serviceUuid));
  }
  advertisement.setAppearance(config.appearance);

  BLEAdvertisementData scanResponse;
  scanResponse.setName(config.deviceName);

  advertising->setAdvertisementType(ADV_TYPE_IND);
  advertising->setScanResponse(true);
  advertising->setAdvertisementData(advertisement);
  advertising->setScanResponseData(scanResponse);
}

void BleCommandChannel::publish(const String& message) {
  if (txCharacteristic_ == nullptr) {
    return;
  }

  txCharacteristic_->setValue(message.c_str());
  txCharacteristic_->notify();
}

}  // namespace agentlight
