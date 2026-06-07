#include "agentlight/domain/LightState.h"

namespace agentlight {

namespace {

String normalize(const String& value) {
  String normalized = value;
  normalized.trim();
  normalized.toUpperCase();
  return normalized;
}

}  // namespace

const char* toText(LightState state) {
  switch (state) {
    case LightState::Green:
      return "GREEN";
    case LightState::Yellow:
      return "YELLOW";
    case LightState::Red:
      return "RED";
    case LightState::Off:
    default:
      return "OFF";
  }
}

bool tryParseLightState(const String& value, LightState& state) {
  const String normalized = normalize(value);

  if (normalized == "GREEN") {
    state = LightState::Green;
    return true;
  }
  if (normalized == "YELLOW" || normalized == "AMBER") {
    state = LightState::Yellow;
    return true;
  }
  if (normalized == "RED") {
    state = LightState::Red;
    return true;
  }
  if (normalized == "OFF") {
    state = LightState::Off;
    return true;
  }

  return false;
}

}  // namespace agentlight

