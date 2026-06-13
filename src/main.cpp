/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include <Arduino.h>

#include "agentlight/application/StatusLightService.h"
#include "agentlight/infrastructure/BleCommandChannel.h"
#include "agentlight/infrastructure/GpioLightDriver.h"
#include "agentlight/infrastructure/UsbCommandChannel.h"
#include "agentlight/infrastructure/WifiCommandChannel.h"

#ifndef AGENTLIGHT_PIN_RED
#define AGENTLIGHT_PIN_RED 4
#endif

#ifndef AGENTLIGHT_PIN_YELLOW
#define AGENTLIGHT_PIN_YELLOW 5
#endif

#ifndef AGENTLIGHT_PIN_GREEN
#define AGENTLIGHT_PIN_GREEN 6
#endif

#ifndef AGENTLIGHT_ACTIVE_LOW
#define AGENTLIGHT_ACTIVE_LOW 1
#endif

#ifndef AGENTLIGHT_WIFI_AP_SSID
#define AGENTLIGHT_WIFI_AP_SSID "WHALESKY-LABS-AGENTLIGHT"
#endif

#ifndef AGENTLIGHT_WIFI_AP_PASSWORD
#define AGENTLIGHT_WIFI_AP_PASSWORD "12345678"
#endif

#ifndef AGENTLIGHT_BLE_DEVICE_NAME
#define AGENTLIGHT_BLE_DEVICE_NAME "WHALESKY-LABS-AGENTLIGHT"
#endif

#ifndef AGENTLIGHT_BLE_ADVERTISED_NAME
#define AGENTLIGHT_BLE_ADVERTISED_NAME "AGENTLIGHT"
#endif

#ifndef AGENTLIGHT_BLE_SERVICE_UUID
#define AGENTLIGHT_BLE_SERVICE_UUID "8f16d7a0-6c6d-4d68-8d64-6b4d2a86b601"
#endif

#ifndef AGENTLIGHT_BLE_RX_UUID
#define AGENTLIGHT_BLE_RX_UUID "8f16d7a1-6c6d-4d68-8d64-6b4d2a86b601"
#endif

#ifndef AGENTLIGHT_BLE_TX_UUID
#define AGENTLIGHT_BLE_TX_UUID "8f16d7a2-6c6d-4d68-8d64-6b4d2a86b601"
#endif

#ifndef AGENTLIGHT_BLE_APPEARANCE
#define AGENTLIGHT_BLE_APPEARANCE 0x03C0
#endif

#ifndef AGENTLIGHT_BLE_ENABLE_HID_PAIRING_SHELL
#define AGENTLIGHT_BLE_ENABLE_HID_PAIRING_SHELL 1
#endif

#ifndef AGENTLIGHT_BLE_MANUFACTURER_NAME
#define AGENTLIGHT_BLE_MANUFACTURER_NAME "whalesky-labs"
#endif

#ifndef AGENTLIGHT_BLE_MODEL_NUMBER
#define AGENTLIGHT_BLE_MODEL_NUMBER "AgentLight-ESP32-C3"
#endif

#ifndef AGENTLIGHT_BLE_BATTERY_LEVEL
#define AGENTLIGHT_BLE_BATTERY_LEVEL 100
#endif

#ifndef AGENTLIGHT_BLE_VENDOR_ID
#define AGENTLIGHT_BLE_VENDOR_ID 0x1209
#endif

#ifndef AGENTLIGHT_BLE_PRODUCT_ID
#define AGENTLIGHT_BLE_PRODUCT_ID 0xA11E
#endif

#ifndef AGENTLIGHT_BLE_PRODUCT_VERSION
#define AGENTLIGHT_BLE_PRODUCT_VERSION 0x0100
#endif

#ifndef AGENTLIGHT_BLE_REQUIRE_PAIRING
#define AGENTLIGHT_BLE_REQUIRE_PAIRING 1
#endif

#ifndef AGENTLIGHT_BLE_PAIRING_PIN
#define AGENTLIGHT_BLE_PAIRING_PIN 123456
#endif

namespace {

agentlight::GpioLightDriver lightDriver(
    AGENTLIGHT_PIN_RED,
    AGENTLIGHT_PIN_YELLOW,
    AGENTLIGHT_PIN_GREEN,
    AGENTLIGHT_ACTIVE_LOW == 1);

agentlight::StatusLightService statusLight(lightDriver);
agentlight::UsbCommandChannel usbChannel;
agentlight::BleCommandChannel bleChannel;
agentlight::WifiCommandChannel wifiChannel;
agentlight::BleCommandChannelConfig bleConfig{
    AGENTLIGHT_BLE_DEVICE_NAME,
    AGENTLIGHT_BLE_ADVERTISED_NAME,
    AGENTLIGHT_BLE_SERVICE_UUID,
    AGENTLIGHT_BLE_RX_UUID,
    AGENTLIGHT_BLE_TX_UUID,
    AGENTLIGHT_BLE_APPEARANCE,
    {
        AGENTLIGHT_BLE_REQUIRE_PAIRING == 1,
        AGENTLIGHT_BLE_PAIRING_PIN,
    },
    {
        AGENTLIGHT_BLE_ENABLE_HID_PAIRING_SHELL == 1,
        AGENTLIGHT_BLE_MANUFACTURER_NAME,
        AGENTLIGHT_BLE_MODEL_NUMBER,
        AGENTLIGHT_BLE_BATTERY_LEVEL,
        AGENTLIGHT_BLE_VENDOR_ID,
        AGENTLIGHT_BLE_PRODUCT_ID,
        AGENTLIGHT_BLE_PRODUCT_VERSION,
    },
};

String handleCommand(const String& command) {
  return statusLight.handleCommand(command);
}

}  // namespace

void setup() {
  lightDriver.begin();
  statusLight.begin({agentlight::LightState::Off, agentlight::LightEffect::Steady});

  usbChannel.begin(115200);
  delay(300);
  Serial.println("AgentLight ready. Commands: GREEN YELLOW RED OFF PING STATUS HELP");

  bleChannel.begin(bleConfig, handleCommand);
  wifiChannel.begin(AGENTLIGHT_WIFI_AP_SSID, AGENTLIGHT_WIFI_AP_PASSWORD, handleCommand);
  Serial.print("BLE pairing ");
  Serial.println(bleConfig.security.requirePairing ? "required" : "disabled");
  if (bleConfig.security.requirePairing) {
    Serial.print("BLE pairing PIN: ");
    Serial.println(bleConfig.security.pairingPin);
  }
  Serial.print("Wi-Fi AP ready: ");
  Serial.println(AGENTLIGHT_WIFI_AP_SSID);
  Serial.println("Wi-Fi API: http://192.168.4.1/status");
}

void loop() {
  usbChannel.poll(handleCommand);
  wifiChannel.poll();
  statusLight.tick(millis());
  delay(5);
}
