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
    let messageCategory: String
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

let notificationFreshnessSeconds: TimeInterval = 60
let notificationReadLimit = 50
let messageCategoryOrder = ["group", "friend", "other"]

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

func recentWeChatNotifications(limit: Int = notificationReadLimit) -> [NotificationSignal] {
    var db: OpaquePointer?
    let path = userNotificationDatabasePath()
    let openResult = sqlite3_open_v2(
        "file:\(path)?mode=ro",
        &db,
        SQLITE_OPEN_READONLY | SQLITE_OPEN_URI,
        nil
    )
    guard openResult == SQLITE_OK, let database = db else {
        return []
    }
    defer { sqlite3_close(database) }

    let sql = """
        SELECT r.data, r.delivered_date
        FROM record r
        JOIN app a ON a.app_id = r.app_id
        WHERE a.identifier = 'com.tencent.xinwechat'
        ORDER BY r.delivered_date DESC, r.rec_id DESC
        LIMIT ?
        """
    var statement: OpaquePointer?
    guard sqlite3_prepare_v2(database, sql, -1, &statement, nil) == SQLITE_OK, let query = statement else {
        return []
    }
    defer { sqlite3_finalize(query) }
    sqlite3_bind_int(query, 1, Int32(limit))

    var notifications: [NotificationSignal] = []
    while sqlite3_step(query) == SQLITE_ROW {
        guard let blob = sqlite3_column_blob(query, 0) else {
            continue
        }

        let byteCount = Int(sqlite3_column_bytes(query, 0))
        let notificationDate = Date(timeIntervalSinceReferenceDate: sqlite3_column_double(query, 1))
        let data = Data(bytes: blob, count: byteCount)
        if let notification = decodeNotificationSignal(data: data, deliveredAt: notificationDate) {
            notifications.append(notification)
        }
    }
    return notifications
}

func latestWeChatNotification() -> NotificationSignal? {
    return recentWeChatNotifications(limit: 1).first
}

func decodeNotificationSignal(data: Data, deliveredAt notificationDate: Date) -> NotificationSignal? {
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

func isFresh(_ notification: NotificationSignal) -> Bool {
    let age = Date().timeIntervalSince(notification.deliveredAt)
    return age >= -5 && age <= notificationFreshnessSeconds
}

func messageCategory(identifier: String, conversation: String, sender: String) -> String {
    let searchable = "\(identifier) \(conversation) \(sender)".lowercased()
    if searchable.contains("@chatroom") {
        return "group"
    }
    if searchable.contains("wxid_") {
        return "friend"
    }
    return "other"
}

func notificationsByCategory(_ notifications: [NotificationSignal]) -> [NotificationSignal] {
    var byCategory: [String: NotificationSignal] = [:]
    for notification in notifications {
        let category = messageCategory(
            identifier: notification.identifier,
            conversation: notification.conversation,
            sender: notification.conversation
        )
        if byCategory[category] == nil {
            byCategory[category] = notification
        }
    }
    return messageCategoryOrder.compactMap { byCategory[$0] }
}

func emitNotificationMessage(
    _ notification: NotificationSignal,
    confidence: String,
    capabilities: [String]
) {
    let category = messageCategory(
        identifier: notification.identifier,
        conversation: notification.conversation,
        sender: notification.conversation
    )
    emit(Payload(
        source: "wechat",
        event: "wechat-message",
        platform: "macos",
        identifier: notification.identifier,
        conversation: notification.conversation,
        sender: notification.conversation,
        summary: notification.summary,
        messageCategory: category,
        confidence: confidence,
        diagnostic: "",
        capabilities: capabilities,
        timestamp: timestamp()
    ))
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
            messageCategory: "",
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
            messageCategory: "",
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
            messageCategory: "",
            confidence: title.isEmpty ? "unread-only" : "conversation-title",
            diagnostic: "",
            capabilities: ["process-running", "accessibility", "conversation-title"],
            timestamp: timestamp()
        ))
        return 0
    }

    let notifications = recentWeChatNotifications()
    let freshNotifications = notificationsByCategory(notifications.filter(isFresh))
    if !freshNotifications.isEmpty {
        for notification in freshNotifications {
            emitNotificationMessage(
                notification,
                confidence: "notification-center",
                capabilities: ["process-running", "accessibility", "unread-navigation", "notification-center", "notification-user-info"]
            )
        }
        return 0
    }

    let category = messageCategory(identifier: "", conversation: title, sender: "")
    let notificationCapabilities = notifications.isEmpty ? [] : ["notification-stale"]
    emit(Payload(
        source: "wechat",
        event: "wechat-message",
        platform: "macos",
        identifier: "",
        conversation: title,
        sender: "",
        summary: isNavigationUnreadHint(signal) ? "" : signal,
        messageCategory: category,
        confidence: isNavigationUnreadHint(signal) ? "unread-only" : "visible-summary",
        diagnostic: "",
        capabilities: (isNavigationUnreadHint(signal)
            ? ["process-running", "accessibility", "unread-navigation"]
            : ["process-running", "accessibility", "visible-summary"]) + notificationCapabilities,
        timestamp: timestamp()
    ))
    return 0
}

exit(main())
