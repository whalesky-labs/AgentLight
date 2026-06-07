#include <Arduino.h>

#include "agentlight/application/StatusLightService.h"
#include "agentlight/infrastructure/BleCommandChannel.h"
#include "agentlight/infrastructure/GpioLightDriver.h"
#include "agentlight/infrastructure/UsbCommandChannel.h"

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

namespace {

agentlight::GpioLightDriver lightDriver(
    AGENTLIGHT_PIN_RED,
    AGENTLIGHT_PIN_YELLOW,
    AGENTLIGHT_PIN_GREEN,
    AGENTLIGHT_ACTIVE_LOW == 1);

agentlight::StatusLightService statusLight(lightDriver);
agentlight::UsbCommandChannel usbChannel;
agentlight::BleCommandChannel bleChannel;

String handleCommand(const String& command) {
  return statusLight.handleCommand(command);
}

}  // namespace

void setup() {
  lightDriver.begin();
  statusLight.begin(agentlight::LightState::Off);

  usbChannel.begin(115200);
  delay(300);
  Serial.println("AgentLight ready. Commands: GREEN YELLOW RED OFF PING STATUS HELP");

  bleChannel.begin("AgentLight", handleCommand);
}

void loop() {
  usbChannel.poll(handleCommand);
  delay(5);
}
