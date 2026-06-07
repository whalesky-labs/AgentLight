#include "agentlight/infrastructure/WifiCommandChannel.h"

#include <WiFi.h>

namespace agentlight {

WifiCommandChannel::WifiCommandChannel(uint16_t port) : server_(port) {}

void WifiCommandChannel::begin(const char* apSsid, const char* apPassword, String (*handler)(const String& command)) {
  handler_ = handler;

  WiFi.mode(WIFI_AP);
  WiFi.softAP(apSsid, apPassword);

  registerRoutes();
  server_.begin();
}

void WifiCommandChannel::poll() {
  server_.handleClient();
}

void WifiCommandChannel::registerRoutes() {
  server_.on("/", HTTP_GET, [this]() { handleRoot(); });
  server_.on("/status", HTTP_GET, [this]() { handleStatus(); });
  server_.on("/command", HTTP_GET, [this]() { handleCommand(); });
  server_.on("/command", HTTP_POST, [this]() { handleCommand(); });
  server_.on("/command", HTTP_OPTIONS, [this]() { handleOptions(); });
  server_.onNotFound([this]() { handleNotFound(); });
}

void WifiCommandChannel::handleRoot() {
  sendText(
      200,
      "AgentLight Wi-Fi channel\n"
      "GET /status\n"
      "GET /command?cmd=GREEN\n"
      "POST /command with plain text command\n");
}

void WifiCommandChannel::handleStatus() {
  if (handler_ == nullptr) {
    sendText(503, "ERR HANDLER_NOT_READY");
    return;
  }

  sendText(200, handler_("STATUS"));
}

void WifiCommandChannel::handleCommand() {
  if (handler_ == nullptr) {
    sendText(503, "ERR HANDLER_NOT_READY");
    return;
  }

  const String command = extractCommand();
  if (command.length() == 0) {
    sendText(400, "ERR MISSING_COMMAND");
    return;
  }

  sendText(200, handler_(command));
}

void WifiCommandChannel::handleOptions() {
  server_.sendHeader("Access-Control-Allow-Origin", "*");
  server_.sendHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  server_.sendHeader("Access-Control-Allow-Headers", "Content-Type");
  server_.send(204);
}

void WifiCommandChannel::handleNotFound() {
  sendText(404, "ERR NOT_FOUND");
}

void WifiCommandChannel::sendText(int statusCode, const String& body) {
  server_.sendHeader("Access-Control-Allow-Origin", "*");
  server_.send(statusCode, "text/plain; charset=utf-8", body);
}

String WifiCommandChannel::extractCommand() {
  String command;

  if (server_.hasArg("cmd")) {
    command = server_.arg("cmd");
  } else if (server_.hasArg("value")) {
    command = server_.arg("value");
  } else if (server_.hasArg("plain")) {
    command = server_.arg("plain");
  } else if (server_.args() > 0) {
    command = server_.arg(0);
  }

  command.trim();
  return command;
}

}  // namespace agentlight
