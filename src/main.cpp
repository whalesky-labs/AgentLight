/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight
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
#define AGENTLIGHT_ACTIVE_LOW 0
#endif

#ifndef AGENTLIGHT_WIFI_AP_SSID
#define AGENTLIGHT_WIFI_AP_SSID "WHALESKY-LABS-AGENTLIGHT"
#endif

#ifndef AGENTLIGHT_WIFI_AP_PASSWORD
#define AGENTLIGHT_WIFI_AP_PASSWORD "agentlight"
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

  bleChannel.begin("WHALESKY-LABS-AGENTLIGHT", handleCommand);
  wifiChannel.begin(AGENTLIGHT_WIFI_AP_SSID, AGENTLIGHT_WIFI_AP_PASSWORD, handleCommand);
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
