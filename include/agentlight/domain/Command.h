/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight
 */

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
  LightPattern pattern;
  String raw;
};

Command parseCommand(const String& line);

}  // namespace agentlight
