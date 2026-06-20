#!/usr/bin/env swift
//
// This file is part of AgentLight.
//
// @link     https://github.com/whalesky-labs/AgentLight
// @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
// @contact  root@imoi.cn
// @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
//

import AppKit
import ApplicationServices
import Foundation

struct Payload: Encodable {
    let source: String
    let event: String
    let platform: String
    let conversation: String
    let sender: String
    let summary: String
    let confidence: String
    let diagnostic: String
    let capabilities: [String]
    let timestamp: String
}

func timestamp() -> String {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withTimeZone]
    return formatter.string(from: Date())
}

func emit(_ payload: Payload) {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.withoutEscapingSlashes]
    if let data = try? encoder.encode(payload), let line = String(data: data, encoding: .utf8) {
        print(line)
    }
}

func runningWeChatApps() -> [NSRunningApplication] {
    NSWorkspace.shared.runningApplications.filter { app in
        let name = (app.localizedName ?? "").lowercased()
        let bundle = (app.bundleIdentifier ?? "").lowercased()
        return name.contains("wechat") || name.contains("微信") || bundle.contains("wechat") || bundle.contains("weixin")
    }
}

func accessibilityTrusted() -> Bool {
    let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: false] as CFDictionary
    return AXIsProcessTrustedWithOptions(options)
}

func stringAttribute(_ element: AXUIElement, _ attribute: String) -> String {
    var value: CFTypeRef?
    let result = AXUIElementCopyAttributeValue(element, attribute as CFString, &value)
    if result == .success, let text = value as? String {
        return text
    }
    return ""
}

func children(_ element: AXUIElement) -> [AXUIElement] {
    var value: CFTypeRef?
    let result = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &value)
    if result == .success, let items = value as? [AXUIElement] {
        return items
    }
    return []
}

func collectVisibleText(_ element: AXUIElement, limit: Int = 200) -> [String] {
    var output: [String] = []
    var stack: [AXUIElement] = [element]

    while !stack.isEmpty && output.count < limit {
        let current = stack.removeLast()
        for attribute in [kAXTitleAttribute, kAXValueAttribute, kAXDescriptionAttribute, kAXHelpAttribute] {
            let text = stringAttribute(current, attribute as String).trimmingCharacters(in: .whitespacesAndNewlines)
            if !text.isEmpty {
                output.append(text)
            }
        }
        stack.append(contentsOf: children(current))
    }

    return output
}

func unreadSignal(from texts: [String]) -> String {
    let patterns = ["未读", "条新消息", "[有人@我]", "@我", "new message", "unread"]
    for text in texts {
        let lower = text.lowercased()
        if patterns.contains(where: { lower.contains($0.lowercased()) }) {
            return text
        }
    }
    return ""
}

func isNavigationUnreadHint(_ text: String) -> Bool {
    let normalized = text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    let ignored = [
        "显示下一个未读会话",
        "显示上一条未读会话",
        "show next unread conversation",
        "show previous unread conversation",
    ]
    return ignored.contains(normalized)
}

func main() -> Int32 {
    let apps = runningWeChatApps()
    guard let app = apps.first else {
        emit(Payload(
            source: "wechat",
            event: "wechat-offline",
            platform: "macos",
            conversation: "",
            sender: "",
            summary: "",
            confidence: "diagnostic",
            diagnostic: "WeChat process is not running",
            capabilities: [],
            timestamp: timestamp()
        ))
        return 0
    }

    if !accessibilityTrusted() {
        emit(Payload(
            source: "wechat",
            event: "wechat-listener-error",
            platform: "macos",
            conversation: "",
            sender: "",
            summary: "",
            confidence: "diagnostic",
            diagnostic: "Accessibility permission is not granted",
            capabilities: ["process-running"],
            timestamp: timestamp()
        ))
        return 0
    }

    let axApp = AXUIElementCreateApplication(app.processIdentifier)
    let texts = collectVisibleText(axApp)
    let signal = unreadSignal(from: texts)
    let title = texts.first ?? ""

    if signal.isEmpty {
        emit(Payload(
            source: "wechat",
            event: "wechat-cleared",
            platform: "macos",
            conversation: title,
            sender: "",
            summary: "",
            confidence: title.isEmpty ? "unread-only" : "conversation-title",
            diagnostic: "",
            capabilities: ["process-running", "accessibility", "conversation-title"],
            timestamp: timestamp()
        ))
        return 0
    }

    emit(Payload(
        source: "wechat",
        event: "wechat-message",
        platform: "macos",
        conversation: title,
        sender: "",
        summary: isNavigationUnreadHint(signal) ? "" : signal,
        confidence: isNavigationUnreadHint(signal) ? "unread-only" : "visible-summary",
        diagnostic: "",
        capabilities: isNavigationUnreadHint(signal)
            ? ["process-running", "accessibility", "unread-navigation"]
            : ["process-running", "accessibility", "visible-summary"],
        timestamp: timestamp()
    ))
    return 0
}

exit(main())
