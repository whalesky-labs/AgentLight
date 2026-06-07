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

  LightState state = LightState::Off;
  if (tryParseLightState(normalized, state)) {
    return {CommandType::SetLight, state, normalized};
  }

  if (normalized == "PING") {
    return {CommandType::Ping, LightState::Off, normalized};
  }
  if (normalized == "STATUS") {
    return {CommandType::Status, LightState::Off, normalized};
  }
  if (normalized == "HELP" || normalized == "?") {
    return {CommandType::Help, LightState::Off, normalized};
  }

  return {CommandType::Unknown, LightState::Off, normalized};
}

}  // namespace agentlight

