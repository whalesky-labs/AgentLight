#pragma once

#include <Arduino.h>
#include "agentlight/domain/LightState.h"

namespace agentlight {

enum class CommandType {
  SetLight,
  Ping,
  Status,
  Help,
  Unknown,
};

struct Command {
  CommandType type;
  LightState state;
  String raw;
};

Command parseCommand(const String& line);

}  // namespace agentlight

