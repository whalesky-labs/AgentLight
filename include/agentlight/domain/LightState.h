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
  All,
};

enum class LightEffect {
  Off,
  Steady,
  Blink,
  Breathe,
};

struct LightPattern {
  LightState state;
  LightEffect effect;
};

struct LightChannels {
  LightEffect red;
  LightEffect yellow;
  LightEffect green;
};

const char* toText(LightState state);
const char* toText(LightEffect effect);
String toText(const LightPattern& pattern);
String toText(const LightChannels& channels);
LightChannels channelsFromPattern(const LightPattern& pattern);
bool tryParseLightPattern(const String& value, LightPattern& pattern);
bool tryParseLightChannels(const String& value, LightChannels& channels);

}  // namespace agentlight
