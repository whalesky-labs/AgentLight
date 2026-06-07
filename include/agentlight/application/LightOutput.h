#pragma once

#include "agentlight/domain/LightState.h"

namespace agentlight {

class LightOutput {
 public:
  virtual ~LightOutput() = default;
  virtual void setLight(LightState state) = 0;
};

}  // namespace agentlight

