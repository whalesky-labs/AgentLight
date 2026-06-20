/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
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
    case LightState::All:
      return "ALL";
    case LightState::Off:
    default:
      return "OFF";
  }
}

const char* toText(LightEffect effect) {
  switch (effect) {
    case LightEffect::Off:
      return "OFF";
    case LightEffect::Blink:
      return "BLINK";
    case LightEffect::Breathe:
      return "BREATHE";
    case LightEffect::Steady:
    default:
      return "STEADY";
  }
}

String toText(const LightChannels& channels) {
  return String("LANES:RED=") + toText(channels.red) + ",YELLOW=" + toText(channels.yellow) + ",GREEN=" +
         toText(channels.green);
}

LightChannels channelsFromPattern(const LightPattern& pattern) {
  const LightEffect effect = pattern.state == LightState::Off ? LightEffect::Off : pattern.effect;
  LightChannels channels = {LightEffect::Off, LightEffect::Off, LightEffect::Off};

  switch (pattern.state) {
    case LightState::Red:
      channels.red = effect;
      break;
    case LightState::Yellow:
      channels.yellow = effect;
      break;
    case LightState::Green:
      channels.green = effect;
      break;
    case LightState::All:
      channels.red = effect;
      channels.yellow = effect;
      channels.green = effect;
      break;
    case LightState::Off:
    default:
      break;
  }

  return channels;
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

bool tryParseLightEffect(const String& value, LightEffect& effect) {
  const String normalized = normalize(value);

  if (normalized == "OFF") {
    effect = LightEffect::Off;
    return true;
  }
  if (normalized == "STEADY" || normalized == "ON") {
    effect = LightEffect::Steady;
    return true;
  }
  if (normalized == "BLINK") {
    effect = LightEffect::Blink;
    return true;
  }
  if (normalized == "BREATHE") {
    effect = LightEffect::Breathe;
    return true;
  }

  return false;
}

bool tryParseLightChannels(const String& value, LightChannels& channels) {
  const String normalized = normalize(value);
  String payload;
  if (normalized.startsWith("LANES:")) {
    payload = normalized.substring(6);
  } else if (normalized.startsWith("CHANNELS:")) {
    payload = normalized.substring(9);
  } else {
    return false;
  }

  LightChannels next = {LightEffect::Off, LightEffect::Off, LightEffect::Off};
  while (payload.length() > 0) {
    const int comma = payload.indexOf(',');
    const String part = comma >= 0 ? payload.substring(0, comma) : payload;
    payload = comma >= 0 ? payload.substring(comma + 1) : "";

    const int equals = part.indexOf('=');
    if (equals <= 0) {
      return false;
    }

    const String key = part.substring(0, equals);
    const String effectValue = part.substring(equals + 1);
    LightEffect effect = LightEffect::Off;
    if (!tryParseLightEffect(effectValue, effect)) {
      return false;
    }

    if (key == "RED") {
      next.red = effect;
    } else if (key == "YELLOW" || key == "AMBER") {
      next.yellow = effect;
    } else if (key == "GREEN") {
      next.green = effect;
    } else {
      return false;
    }
  }

  channels = next;
  return true;
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
  if (normalized == "ALL") {
    pattern = {LightState::All, LightEffect::Steady};
    return true;
  }
  if (normalized == "ALL_BLINK") {
    pattern = {LightState::All, LightEffect::Blink};
    return true;
  }
  if (normalized == "ALL_BREATHE") {
    pattern = {LightState::All, LightEffect::Breathe};
    return true;
  }
  if (normalized == "OFF") {
    pattern = {LightState::Off, LightEffect::Steady};
    return true;
  }

  return false;
}

}  // namespace agentlight
