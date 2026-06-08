/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight
 */

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

const char* toText(LightEffect effect) {
  switch (effect) {
    case LightEffect::Blink:
      return "BLINK";
    case LightEffect::Breathe:
      return "BREATHE";
    case LightEffect::Steady:
    default:
      return "STEADY";
  }
}

String toText(const LightPattern& pattern) {
  if (pattern.state == LightState::Off) {
    return "OFF";
  }

  if (pattern.effect == LightEffect::Steady) {
    return toText(pattern.state);
  }

  return String(toText(pattern.state)) + "_" + toText(pattern.effect);
}

bool tryParseLightPattern(const String& value, LightPattern& pattern) {
  const String normalized = normalize(value);

  if (normalized == "GREEN") {
    pattern = {LightState::Green, LightEffect::Steady};
    return true;
  }
  if (normalized == "GREEN_BLINK") {
    pattern = {LightState::Green, LightEffect::Blink};
    return true;
  }
  if (normalized == "GREEN_BREATHE") {
    pattern = {LightState::Green, LightEffect::Breathe};
    return true;
  }
  if (normalized == "YELLOW" || normalized == "AMBER") {
    pattern = {LightState::Yellow, LightEffect::Steady};
    return true;
  }
  if (normalized == "YELLOW_BLINK" || normalized == "AMBER_BLINK") {
    pattern = {LightState::Yellow, LightEffect::Blink};
    return true;
  }
  if (normalized == "YELLOW_BREATHE" || normalized == "AMBER_BREATHE") {
    pattern = {LightState::Yellow, LightEffect::Breathe};
    return true;
  }
  if (normalized == "RED") {
    pattern = {LightState::Red, LightEffect::Steady};
    return true;
  }
  if (normalized == "RED_BLINK") {
    pattern = {LightState::Red, LightEffect::Blink};
    return true;
  }
  if (normalized == "RED_BREATHE") {
    pattern = {LightState::Red, LightEffect::Breathe};
    return true;
  }
  if (normalized == "OFF") {
    pattern = {LightState::Off, LightEffect::Steady};
    return true;
  }

  return false;
}

}  // namespace agentlight
