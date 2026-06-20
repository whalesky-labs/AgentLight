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
import SQLite3

struct Payload: Encodable {
    let source: String
    let event: String
    let platform: String
    let identifier: String
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

struct NotificationSignal {
    let identifier: String
    let conversation: String
    let summary: String
    let deliveredAt: Date
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

func userNotificationDatabasePath() -> String {
    let home = FileManager.default.homeDirectoryForCurrentUser.path
    return "\(home)/Library/Group Containers/group.com.apple.usernoted/db2/db"
}

func latestWeChatNotification() -> NotificationSignal? {
    var db: OpaquePointer?
    let path = userNotificationDatabasePath()
    let openResult = sqlite3_open_v2(
        "file:\(path)?mode=ro",
        &db,
        SQLITE_OPEN_READONLY | SQLITE_OPEN_URI,
        nil
    )
    guard openResult == SQLITE_OK, let database = db else {
        return nil
    }
    defer { sqlite3_close(database) }

    let sql = """
        SELECT r.data, r.delivered_date
        FROM record r
        JOIN app a ON a.app_id = r.app_id
        WHERE a.identifier = 'com.tencent.xinwechat'
        ORDER BY r.delivered_date DESC, r.rec_id DESC
        LIMIT 1
        """
    var statement: OpaquePointer?
    guard sqlite3_prepare_v2(database, sql, -1, &statement, nil) == SQLITE_OK, let query = statement else {
        return nil
    }
    defer { sqlite3_finalize(query) }

    guard sqlite3_step(query) == SQLITE_ROW else {
        return nil
    }
    guard let blob = sqlite3_column_blob(query, 0) else {
        return nil
    }

    let byteCount = Int(sqlite3_column_bytes(query, 0))
    let notificationDate = Date(timeIntervalSinceReferenceDate: sqlite3_column_double(query, 1))
    let data = Data(bytes: blob, count: byteCount)
    guard
        let plist = try? PropertyListSerialization.propertyList(from: data, options: [], format: nil),
        let root = plist as? [String: Any],
        let request = root["req"] as? [String: Any]
    else {
        return nil
    }

    let summary = (request["body"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    let iden = (request["iden"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    let userInfo = decodeNotificationUserInfo(request["usda"] as? Data)
    let uniqueId = (userInfo["unique_id"] ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    let chatName = (userInfo["chatname"] ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    let identifier = firstNonEmpty([uniqueId, iden, rootUuid(root["uuid"])])
    let conversation = firstNonEmpty([chatName, stripNotificationSuffix(iden), identifier])

    guard !identifier.isEmpty || !conversation.isEmpty || !summary.isEmpty else {
        return nil
    }

    return NotificationSignal(
        identifier: identifier,
        conversation: conversation,
        summary: summary,
        deliveredAt: notificationDate
    )
}

func decodeNotificationUserInfo(_ data: Data?) -> [String: String] {
    guard let data else {
        return [:]
    }
    guard
        let object = try? NSKeyedUnarchiver.unarchivedObject(ofClasses: [NSDictionary.self, NSString.self], from: data),
        let dictionary = object as? [String: Any]
    else {
        return [:]
    }
    var output: [String: String] = [:]
    for (key, value) in dictionary {
        if let text = value as? String {
            output[key] = text
        }
    }
    return output
}

func rootUuid(_ value: Any?) -> String {
    guard let data = value as? Data else {
        return ""
    }
    return data.map { String(format: "%02x", $0) }.joined()
}

func firstNonEmpty(_ values: [String]) -> String {
    for value in values {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty {
            return trimmed
        }
    }
    return ""
}

func stripNotificationSuffix(_ identifier: String) -> String {
    let trimmed = identifier.trimmingCharacters(in: .whitespacesAndNewlines)
    let pattern = #"_(\d+)_(\d+)$"#
    if let regex = try? NSRegularExpression(pattern: pattern),
       let match = regex.firstMatch(in: trimmed, range: NSRange(trimmed.startIndex..., in: trimmed)),
       let range = Range(match.range, in: trimmed) {
        return String(trimmed[..<range.lowerBound])
    }
    return trimmed
}

func main() -> Int32 {
    let apps = runningWeChatApps()
    guard let app = apps.first else {
        emit(Payload(
            source: "wechat",
            event: "wechat-offline",
            platform: "macos",
            identifier: "",
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
            identifier: "",
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
            identifier: "",
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

    if let notification = latestWeChatNotification() {
        emit(Payload(
            source: "wechat",
            event: "wechat-message",
            platform: "macos",
            identifier: notification.identifier,
            conversation: notification.conversation,
            sender: notification.conversation,
            summary: notification.summary,
            confidence: "notification-center",
            diagnostic: "",
            capabilities: ["process-running", "accessibility", "unread-navigation", "notification-center", "notification-user-info"],
            timestamp: timestamp()
        ))
        return 0
    }

    emit(Payload(
        source: "wechat",
        event: "wechat-message",
        platform: "macos",
        identifier: "",
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
