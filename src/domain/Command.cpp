/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight
 */

#include "agentlight/domain/Command.h"

namespace agentlight {

namespace {

String normalize(const String& value) {
  String normalized = value;
  normalized.trim();
  normalized.toUpperCase();
  return normalized;
}

}  // namespace

Command parseCommand(const String& line) {
  const String normalized = normalize(line);

  LightPattern pattern = {LightState::Off, LightEffect::Steady};
  if (tryParseLightPattern(normalized, pattern)) {
    return {CommandType::SetLight, pattern, normalized};
  }

  if (normalized == "PING") {
    return {CommandType::Ping, pattern, normalized};
  }
  if (normalized == "STATUS") {
    return {CommandType::Status, pattern, normalized};
  }
  if (normalized == "HELP" || normalized == "?") {
    return {CommandType::Help, pattern, normalized};
  }

  return {CommandType::Unknown, pattern, normalized};
}

}  // namespace agentlight
