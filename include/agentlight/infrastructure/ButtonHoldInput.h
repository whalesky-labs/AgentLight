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

namespace agentlight {

struct ButtonHoldInputConfig {
  uint8_t pin;
  bool activeLow;
  uint32_t holdMs;
};

class ButtonHoldInput {
 public:
  void begin(const ButtonHoldInputConfig& config);
  bool poll(uint32_t nowMs);

 private:
  bool pressed() const;

  ButtonHoldInputConfig config_{0, true, 0};
  bool wasPressed_ = false;
  bool emitted_ = false;
  uint32_t pressedAtMs_ = 0;
};

}  // namespace agentlight
