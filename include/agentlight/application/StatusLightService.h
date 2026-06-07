#pragma once

#include <Arduino.h>
#include "agentlight/application/LightOutput.h"
#include "agentlight/domain/LightState.h"

namespace agentlight {

class StatusLightService {
 public:
  explicit StatusLightService(LightOutput& output);

  void begin(LightState initialState);
  String handleCommand(const String& line);
  LightState currentState() const;

 private:
  void setState(LightState state);

  LightOutput& output_;
  LightState currentState_;
};

}  // namespace agentlight

