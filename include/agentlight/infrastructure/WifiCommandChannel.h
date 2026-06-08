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
#include <WebServer.h>

namespace agentlight {

class WifiCommandChannel {
 public:
  explicit WifiCommandChannel(uint16_t port = 80);

  void begin(const char* apSsid, const char* apPassword, String (*handler)(const String& command));
  void poll();

 private:
  void registerRoutes();
  void handleRoot();
  void handleStatus();
  void handleCommand();
  void handleOptions();
  void handleNotFound();
  void sendText(int statusCode, const String& body);
  String extractCommand();

  WebServer server_;
  String (*handler_)(const String& command) = nullptr;
};

}  // namespace agentlight
