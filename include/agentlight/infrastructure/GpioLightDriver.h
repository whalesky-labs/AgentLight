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
#include "agentlight/application/LightOutput.h"

namespace agentlight {

class GpioLightDriver : public LightOutput {
 public:
  GpioLightDriver(uint8_t redPin, uint8_t yellowPin, uint8_t greenPin, bool activeLow);

  void begin();
  void setPattern(const LightPattern& pattern) override;
  void tick(unsigned long nowMs) override;

 private:
  uint8_t pinFor(LightState state) const;
  void writeAllOff();
  void writeAll(bool active);
  void writeAllPwm(uint8_t brightness);
  void writeInactiveOff(uint8_t activePin);
  void releasePwm(uint8_t pin);
  void writeOne(uint8_t pin, bool active);
  void writeOnePwm(uint8_t pin, uint8_t brightness);

  uint8_t redPin_;
  uint8_t yellowPin_;
  uint8_t greenPin_;
  bool activeLow_;
  LightPattern pattern_;
};

}  // namespace agentlight
