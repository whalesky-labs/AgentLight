/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include "agentlight/infrastructure/ButtonHoldInput.h"

namespace agentlight {

void ButtonHoldInput::begin(const ButtonHoldInputConfig& config) {
  config_ = config;
  pinMode(config_.pin, config_.activeLow ? INPUT_PULLUP : INPUT_PULLDOWN);
  wasPressed_ = false;
  emitted_ = false;
  pressedAtMs_ = 0;
}

bool ButtonHoldInput::poll(uint32_t nowMs) {
  const bool isPressed = pressed();
  if (!isPressed) {
    wasPressed_ = false;
    emitted_ = false;
    pressedAtMs_ = 0;
    return false;
  }

  if (!wasPressed_) {
    wasPressed_ = true;
    emitted_ = false;
    pressedAtMs_ = nowMs;
    return false;
  }

  if (emitted_) {
    return false;
  }

  const int32_t heldMs = static_cast<int32_t>(nowMs - pressedAtMs_);
  if (heldMs < static_cast<int32_t>(config_.holdMs)) {
    return false;
  }

  emitted_ = true;
  return true;
}

bool ButtonHoldInput::pressed() const {
  const int level = digitalRead(config_.pin);
  return config_.activeLow ? level == LOW : level == HIGH;
}

}  // namespace agentlight
