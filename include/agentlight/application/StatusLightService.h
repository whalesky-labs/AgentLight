#pragma once

#include <Arduino.h>
#include "agentlight/application/LightOutput.h"
#include "agentlight/domain/LightState.h"

namespace agentlight {

class StatusLightService {
 public:
  explicit StatusLightService(LightOutput& output);

  void begin(const LightPattern& initialPattern);
  void tick(unsigned long nowMs);
  String handleCommand(const String& line);
  LightPattern currentPattern() const;

 private:
  void setPattern(const LightPattern& pattern);

  LightOutput& output_;
  LightPattern currentPattern_;
};

}  // namespace agentlight
