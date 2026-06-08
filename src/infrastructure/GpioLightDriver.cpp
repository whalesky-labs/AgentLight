/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include "agentlight/infrastructure/GpioLightDriver.h"

namespace agentlight {

GpioLightDriver::GpioLightDriver(uint8_t redPin, uint8_t yellowPin, uint8_t greenPin, bool activeLow)
    : redPin_(redPin),
      yellowPin_(yellowPin),
      greenPin_(greenPin),
      activeLow_(activeLow),
      pattern_({LightState::Off, LightEffect::Steady}) {}

void GpioLightDriver::begin() {
  pinMode(redPin_, OUTPUT);
  pinMode(yellowPin_, OUTPUT);
  pinMode(greenPin_, OUTPUT);
  setPattern({LightState::Off, LightEffect::Steady});
}

void GpioLightDriver::setPattern(const LightPattern& pattern) {
  pattern_ = pattern;
  tick(millis());
}

void GpioLightDriver::tick(unsigned long nowMs) {
  const uint8_t activePin = pinFor(pattern_.state);
  if (activePin == 0) {
    writeAllOff();
    return;
  }

  writeInactiveOff(activePin);

  switch (pattern_.effect) {
    case LightEffect::Blink:
      writeOne(activePin, (nowMs % 800) < 400);
      return;
    case LightEffect::Breathe: {
      const uint16_t phase = nowMs % 2000;
      const uint16_t triangle = phase < 1000 ? phase : 2000 - phase;
      const uint8_t brightness = static_cast<uint8_t>(20 + ((triangle * 235UL) / 1000));
      writeOnePwm(activePin, brightness);
      return;
    }
    case LightEffect::Steady:
    default:
      writeOne(activePin, true);
      return;
  }
}

uint8_t GpioLightDriver::pinFor(LightState state) const {
  switch (state) {
    case LightState::Red:
      return redPin_;
    case LightState::Yellow:
      return yellowPin_;
    case LightState::Green:
      return greenPin_;
    case LightState::Off:
    default:
      return 0;
  }
}

void GpioLightDriver::writeAllOff() {
  writeOne(redPin_, false);
  writeOne(yellowPin_, false);
  writeOne(greenPin_, false);
}

void GpioLightDriver::writeInactiveOff(uint8_t activePin) {
  if (redPin_ != activePin) {
    writeOne(redPin_, false);
  }
  if (yellowPin_ != activePin) {
    writeOne(yellowPin_, false);
  }
  if (greenPin_ != activePin) {
    writeOne(greenPin_, false);
  }
}

void GpioLightDriver::writeOne(uint8_t pin, bool active) {
  const uint8_t onLevel = activeLow_ ? LOW : HIGH;
  const uint8_t offLevel = activeLow_ ? HIGH : LOW;
  digitalWrite(pin, active ? onLevel : offLevel);
}

void GpioLightDriver::writeOnePwm(uint8_t pin, uint8_t brightness) {
  analogWrite(pin, activeLow_ ? 255 - brightness : brightness);
}

}  // namespace agentlight
