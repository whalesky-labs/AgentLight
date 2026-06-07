#pragma once

#include <Arduino.h>
#include "agentlight/application/LightOutput.h"

namespace agentlight {

class GpioLightDriver : public LightOutput {
 public:
  GpioLightDriver(uint8_t redPin, uint8_t yellowPin, uint8_t greenPin, bool activeLow);

  void begin();
  void setLight(LightState state) override;

 private:
  void writeOne(uint8_t pin, bool active);

  uint8_t redPin_;
  uint8_t yellowPin_;
  uint8_t greenPin_;
  bool activeLow_;
};

}  // namespace agentlight

