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

namespace agentlight {

enum class LightState {
  Off,
  Red,
  Yellow,
  Green,
};

enum class LightEffect {
  Steady,
  Blink,
  Breathe,
};

struct LightPattern {
  LightState state;
  LightEffect effect;
};

const char* toText(LightState state);
const char* toText(LightEffect effect);
String toText(const LightPattern& pattern);
bool tryParseLightPattern(const String& value, LightPattern& pattern);

}  // namespace agentlight
