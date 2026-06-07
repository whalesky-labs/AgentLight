#include "agentlight/infrastructure/UsbCommandChannel.h"

namespace agentlight {

void UsbCommandChannel::begin(unsigned long baud) {
  Serial.begin(baud);
}

void UsbCommandChannel::poll(String (*handler)(const String& command)) {
  while (Serial.available() > 0) {
    consume(static_cast<char>(Serial.read()), handler);
  }
}

void UsbCommandChannel::consume(char c, String (*handler)(const String& command)) {
  if (c == '\r' || c == '\n') {
    if (buffer_.length() == 0) {
      return;
    }

    const String response = handler(buffer_);
    Serial.println(response);
    buffer_ = "";
    return;
  }

  if (buffer_.length() >= 96) {
    Serial.println("ERR COMMAND_TOO_LONG");
    buffer_ = "";
    return;
  }

  buffer_ += c;
}

}  // namespace agentlight

