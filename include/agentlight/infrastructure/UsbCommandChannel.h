/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight
 */

#pragma once

#include <Arduino.h>

namespace agentlight {

class UsbCommandChannel {
 public:
  void begin(unsigned long baud);
  void poll(String (*handler)(const String& command));

 private:
  void consume(char c, String (*handler)(const String& command));

  String buffer_;
};

}  // namespace agentlight

