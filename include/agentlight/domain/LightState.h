#pragma once

#include <Arduino.h>

namespace agentlight {

enum class LightState {
  Off,
  Red,
  Yellow,
  Green,
};

const char* toText(LightState state);
bool tryParseLightState(const String& value, LightState& state);

}  // namespace agentlight

