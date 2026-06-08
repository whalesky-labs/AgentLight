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
#include "agentlight/application/LightOutput.h"
#include "agentlight/domain/LightState.h"

namespace agentlight {

class StatusLightService {
 public:
  explicit StatusLightService(LightOutput& output);

  void begin(const LightPattern& initialPattern);
  void tick(unsigned long nowMs);
  String handleCommand(const String& line);
  LightPattern currentPattern() const;

 private:
  void setPattern(const LightPattern& pattern);

  LightOutput& output_;
  LightPattern currentPattern_;
};

}  // namespace agentlight
