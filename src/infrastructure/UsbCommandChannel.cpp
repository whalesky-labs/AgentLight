/**
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

#include "agentlight/infrastructure/UsbCommandChannel.h"

namespace agentlight {

void UsbCommandChannel::begin(unsigned long baud) {
  Serial.begin(baud);
}

bool UsbCommandChannel::hostConnected() const {
#if defined(ARDUINO_USB_MODE) && ARDUINO_USB_MODE && defined(ARDUINO_USB_CDC_ON_BOOT) && ARDUINO_USB_CDC_ON_BOOT
  return Serial.isPlugged();
#else
  return true;
#endif
}

bool UsbCommandChannel::poll(String (*handler)(const String& command)) {
  bool handledCommand = false;
  while (Serial.available() > 0) {
    handledCommand = consume(static_cast<char>(Serial.read()), handler) || handledCommand;
  }
  return handledCommand;
}

bool UsbCommandChannel::consume(char c, String (*handler)(const String& command)) {
  if (c == '\r' || c == '\n') {
    if (buffer_.length() == 0) {
      return false;
    }

    const String response = handler(buffer_);
    Serial.println(response);
    buffer_ = "";
    return true;
  }

  if (buffer_.length() >= 96) {
    Serial.println("ERR COMMAND_TOO_LONG");
    buffer_ = "";
    return false;
  }

  buffer_ += c;
  return false;
}

}  // namespace agentlight
