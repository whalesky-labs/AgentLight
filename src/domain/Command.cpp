/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
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
  LightChannels channels = {LightEffect::Off, LightEffect::Off, LightEffect::Off};
  if (tryParseLightChannels(normalized, channels)) {
    return {CommandType::SetLight, pattern, channels, normalized};
  }

  if (tryParseLightPattern(normalized, pattern)) {
    return {CommandType::SetLight, pattern, channelsFromPattern(pattern), normalized};
  }

  if (normalized == "PING") {
    return {CommandType::Ping, pattern, channels, normalized};
  }
  if (normalized == "STATUS") {
    return {CommandType::Status, pattern, channels, normalized};
  }
  if (normalized == "HELP" || normalized == "?") {
    return {CommandType::Help, pattern, channels, normalized};
  }

  return {CommandType::Unknown, pattern, channels, normalized};
}

}  // namespace agentlight
