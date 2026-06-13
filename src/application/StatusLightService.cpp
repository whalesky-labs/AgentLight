/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include "agentlight/application/StatusLightService.h"
#include "agentlight/domain/Command.h"

namespace agentlight {

StatusLightService::StatusLightService(LightOutput& output)
    : output_(output), currentPattern_({LightState::Off, LightEffect::Steady}) {}

void StatusLightService::begin(const LightPattern& initialPattern) {
  setPattern(initialPattern);
}

void StatusLightService::tick(unsigned long nowMs) {
  output_.tick(nowMs);
}

String StatusLightService::handleCommand(const String& line) {
  const Command command = parseCommand(line);

  switch (command.type) {
    case CommandType::SetLight:
      setPattern(command.pattern);
      return String("OK ") + toText(currentPattern_);
    case CommandType::Ping:
      return "PONG";
    case CommandType::Status:
      return String("STATUS ") + toText(currentPattern_);
    case CommandType::Help:
      return "COMMANDS GREEN GREEN_BREATHE GREEN_BLINK YELLOW YELLOW_BREATHE YELLOW_BLINK RED RED_BLINK RED_BREATHE ALL ALL_BLINK ALL_BREATHE OFF PING STATUS HELP";
    case CommandType::Unknown:
    default:
      return String("ERR UNKNOWN_COMMAND ") + command.raw;
  }
}

LightPattern StatusLightService::currentPattern() const {
  return currentPattern_;
}

void StatusLightService::setPattern(const LightPattern& pattern) {
  currentPattern_ = pattern;
  output_.setPattern(pattern);
}

}  // namespace agentlight
