/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#pragma once

#include "agentlight/domain/LightState.h"

namespace agentlight {

class LightOutput {
 public:
  virtual ~LightOutput() = default;
  virtual void setPattern(const LightPattern& pattern) = 0;
  virtual void tick(unsigned long nowMs) = 0;
};

}  // namespace agentlight
