/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight
 */

#include "agentlight/infrastructure/BleCommandChannel.h"

#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

namespace agentlight {

namespace {

constexpr const char* SERVICE_UUID = "8f16d7a0-6c6d-4d68-8d64-6b4d2a86b601";
constexpr const char* RX_UUID = "8f16d7a1-6c6d-4d68-8d64-6b4d2a86b601";
constexpr const char* TX_UUID = "8f16d7a2-6c6d-4d68-8d64-6b4d2a86b601";

class ServerCallbacks : public BLEServerCallbacks {
 public:
  void onConnect(BLEServer* server) override {
    (void)server;
  }

  void onDisconnect(BLEServer* server) override {
    server->startAdvertising();
  }
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

}  // namespace

void BleCommandChannel::begin(const char* deviceName, String (*handler)(const String& command)) {
  BLEDevice::init(deviceName);
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService* service = server->createService(SERVICE_UUID);

  txCharacteristic_ = service->createCharacteristic(
      TX_UUID,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  txCharacteristic_->addDescriptor(new BLE2902());
  txCharacteristic_->setValue("STATUS OFF");

  BLECharacteristic* rxCharacteristic = service->createCharacteristic(
      RX_UUID,
      BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  rxCharacteristic->setCallbacks(new RxCallbacks(*this, handler));

  service->start();

  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  advertising->setScanResponse(true);
  BLEDevice::startAdvertising();
}

void BleCommandChannel::publish(const String& message) {
  if (txCharacteristic_ == nullptr) {
    return;
  }

  txCharacteristic_->setValue(message.c_str());
  txCharacteristic_->notify();
}

}  // namespace agentlight
