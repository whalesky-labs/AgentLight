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
