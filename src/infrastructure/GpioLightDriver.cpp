#include "agentlight/infrastructure/GpioLightDriver.h"

namespace agentlight {

GpioLightDriver::GpioLightDriver(uint8_t redPin, uint8_t yellowPin, uint8_t greenPin, bool activeLow)
    : redPin_(redPin), yellowPin_(yellowPin), greenPin_(greenPin), activeLow_(activeLow) {}

void GpioLightDriver::begin() {
  pinMode(redPin_, OUTPUT);
  pinMode(yellowPin_, OUTPUT);
  pinMode(greenPin_, OUTPUT);
  setLight(LightState::Off);
}

void GpioLightDriver::setLight(LightState state) {
  writeOne(redPin_, state == LightState::Red);
  writeOne(yellowPin_, state == LightState::Yellow);
  writeOne(greenPin_, state == LightState::Green);
}

void GpioLightDriver::writeOne(uint8_t pin, bool active) {
  const uint8_t onLevel = activeLow_ ? LOW : HIGH;
  const uint8_t offLevel = activeLow_ ? HIGH : LOW;
  digitalWrite(pin, active ? onLevel : offLevel);
}

}  // namespace agentlight

