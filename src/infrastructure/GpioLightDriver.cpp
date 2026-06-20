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
      channels_({LightEffect::Off, LightEffect::Off, LightEffect::Off}) {}

void GpioLightDriver::begin() {
  pinMode(redPin_, OUTPUT);
  pinMode(yellowPin_, OUTPUT);
  pinMode(greenPin_, OUTPUT);
  setChannels({LightEffect::Off, LightEffect::Off, LightEffect::Off});
}

void GpioLightDriver::setChannels(const LightChannels& channels) {
  channels_ = channels;
  tick(millis());
}

void GpioLightDriver::tick(unsigned long nowMs) {
  writeChannel(redPin_, channels_.red, nowMs);
  writeChannel(yellowPin_, channels_.yellow, nowMs);
  writeChannel(greenPin_, channels_.green, nowMs);
}

void GpioLightDriver::writeChannel(uint8_t pin, LightEffect effect, unsigned long nowMs) {
  switch (effect) {
    case LightEffect::Off:
      writeOne(pin, false);
      return;
    case LightEffect::Blink: {
      const unsigned long periodMs = pin == yellowPin_ ? 400UL : 800UL;
      writeOne(pin, (nowMs % periodMs) < (periodMs / 2));
      return;
    }
    case LightEffect::Breathe: {
      const uint16_t phase = nowMs % 2000;
      const uint16_t triangle = phase < 1000 ? phase : 2000 - phase;
      const uint8_t brightness = static_cast<uint8_t>(20 + ((triangle * 235UL) / 1000));
      writeOnePwm(pin, brightness);
      return;
    }
    case LightEffect::Steady:
    default:
      writeOne(pin, true);
      return;
  }
}

void GpioLightDriver::writeAllOff() {
  writeAll(false);
}

void GpioLightDriver::writeAll(bool active) {
  writeOne(redPin_, active);
  writeOne(yellowPin_, active);
  writeOne(greenPin_, active);
}

void GpioLightDriver::writeOne(uint8_t pin, bool active) {
  releasePwm(pin);
  const uint8_t onLevel = activeLow_ ? LOW : HIGH;
  const uint8_t offLevel = activeLow_ ? HIGH : LOW;
  digitalWrite(pin, active ? onLevel : offLevel);
}

void GpioLightDriver::releasePwm(uint8_t pin) {
  ledcDetachPin(pin);
  pinMode(pin, OUTPUT);
}

void GpioLightDriver::writeOnePwm(uint8_t pin, uint8_t brightness) {
  analogWrite(pin, activeLow_ ? 255 - brightness : brightness);
}

}  // namespace agentlight
