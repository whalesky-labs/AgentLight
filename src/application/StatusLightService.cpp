#include "agentlight/application/StatusLightService.h"
#include "agentlight/domain/Command.h"

namespace agentlight {

StatusLightService::StatusLightService(LightOutput& output)
    : output_(output), currentState_(LightState::Off) {}

void StatusLightService::begin(LightState initialState) {
  setState(initialState);
}

String StatusLightService::handleCommand(const String& line) {
  const Command command = parseCommand(line);

  switch (command.type) {
    case CommandType::SetLight:
      setState(command.state);
      return String("OK ") + toText(currentState_);
    case CommandType::Ping:
      return "PONG";
    case CommandType::Status:
      return String("STATUS ") + toText(currentState_);
    case CommandType::Help:
      return "COMMANDS GREEN YELLOW RED OFF PING STATUS HELP";
    case CommandType::Unknown:
    default:
      return String("ERR UNKNOWN_COMMAND ") + command.raw;
  }
}

LightState StatusLightService::currentState() const {
  return currentState_;
}

void StatusLightService::setState(LightState state) {
  currentState_ = state;
  output_.setLight(state);
}

}  // namespace agentlight

