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
    : output_(output), currentChannels_({LightEffect::Off, LightEffect::Off, LightEffect::Off}) {}

void StatusLightService::begin(const LightPattern& initialPattern) {
  setChannels(channelsFromPattern(initialPattern));
}

void StatusLightService::tick(unsigned long nowMs) {
  output_.tick(nowMs);
}

String StatusLightService::handleCommand(const String& line) {
  const Command command = parseCommand(line);

  switch (command.type) {
    case CommandType::SetLight:
      setChannels(command.channels);
      return String("OK ") + toText(currentChannels_);
    case CommandType::Ping:
      return "PONG";
    case CommandType::Status:
      return String("STATUS ") + toText(currentChannels_);
    case CommandType::Help:
      return "COMMANDS GREEN GREEN_BREATHE GREEN_BLINK YELLOW YELLOW_BREATHE YELLOW_BLINK RED RED_BLINK RED_BREATHE ALL ALL_BLINK ALL_BREATHE LANES:RED=OFF,YELLOW=BLINK,GREEN=BREATHE OFF PING STATUS HELP";
    case CommandType::Unknown:
    default:
      return String("ERR UNKNOWN_COMMAND ") + command.raw;
  }
}

LightChannels StatusLightService::currentChannels() const {
  return currentChannels_;
}

void StatusLightService::setChannels(const LightChannels& channels) {
  currentChannels_ = channels;
  output_.setChannels(channels);
}

}  // namespace agentlight
