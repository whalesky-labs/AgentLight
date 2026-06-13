/*
 * This file is part of AgentLight.
 *
 * @link     https://github.com/whalesky-labs/AgentLight
 * @document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
 * @contact  root@imoi.cn
 * @license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
 */

import Foundation
import IOKit.hid

struct HidCommandConfig {
    let deviceName: String
    let usagePage: Int
    let usage: Int
    let reportId: Int
    let reportSize: Int
}

enum HidCommandError: Error {
    case deviceNotConnected
    case commandTooLong(Int)
    case openFailed(IOReturn)
    case writeFailed(IOReturn)
    case readFailed(IOReturn)
    case emptyResponse
    case invalidResponse(String)
}

final class SystemBluetoothHidCommand {
    private let config: HidCommandConfig
    private let command: String

    init(config: HidCommandConfig, command: String) {
        self.config = config
        self.command = command
    }

    func run() throws -> String {
        let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
        let matching: [String: Any] = [
            kIOHIDPrimaryUsagePageKey: config.usagePage,
            kIOHIDPrimaryUsageKey: config.usage,
        ]

        IOHIDManagerSetDeviceMatching(manager, matching as CFDictionary)
        IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        defer {
            IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        }

        guard let device = connectedAgentLightDevice(from: manager) else {
            throw HidCommandError.deviceNotConnected
        }

        let openResult = IOHIDDeviceOpen(device, IOOptionBits(kIOHIDOptionsTypeNone))
        guard openResult == kIOReturnSuccess else {
            throw HidCommandError.openFailed(openResult)
        }
        defer {
            IOHIDDeviceClose(device, IOOptionBits(kIOHIDOptionsTypeNone))
        }

        let report = try encodeReport(command)
        let writeResult = report.withUnsafeBufferPointer { pointer in
            IOHIDDeviceSetReport(
                device,
                kIOHIDReportTypeFeature,
                CFIndex(config.reportId),
                pointer.baseAddress!,
                report.count
            )
        }
        guard writeResult == kIOReturnSuccess else {
            throw HidCommandError.writeFailed(writeResult)
        }

        return try waitForAcceptedResponse(from: device)
    }

    private func connectedAgentLightDevice(from manager: IOHIDManager) -> IOHIDDevice? {
        copyDevices(from: manager)
            .filter { propertyString($0, kIOHIDProductKey) == config.deviceName }
            .first
    }

    private func copyDevices(from manager: IOHIDManager) -> [IOHIDDevice] {
        guard let deviceSet = IOHIDManagerCopyDevices(manager) else {
            return []
        }

        let count = CFSetGetCount(deviceSet)
        var values = Array<UnsafeRawPointer?>(repeating: nil, count: count)
        CFSetGetValues(deviceSet, &values)

        return values.compactMap { pointer in
            guard let pointer else {
                return nil
            }

            return unsafeBitCast(pointer, to: IOHIDDevice.self)
        }
    }

    private func encodeReport(_ command: String) throws -> [UInt8] {
        let commandBytes = Array(command.utf8)
        let maxCommandLength = config.reportSize - 1
        guard commandBytes.count <= maxCommandLength else {
            throw HidCommandError.commandTooLong(maxCommandLength)
        }

        var report = Array<UInt8>(repeating: 0, count: config.reportSize + 1)
        report[0] = UInt8(config.reportId)
        report[1] = UInt8(commandBytes.count)
        report.replaceSubrange(2..<(2 + commandBytes.count), with: commandBytes)

        return report
    }

    private func waitForAcceptedResponse(from device: IOHIDDevice) throws -> String {
        var lastResponse = ""
        let deadline = Date().addingTimeInterval(1)

        repeat {
            let response = try readResponse(from: device)
            if isAcceptedResponse(response) {
                return response
            }

            lastResponse = response
            usleep(50_000)
        } while Date() < deadline

        throw HidCommandError.invalidResponse(lastResponse)
    }

    private func readResponse(from device: IOHIDDevice) throws -> String {
        var report = Array<UInt8>(repeating: 0, count: config.reportSize + 1)
        report[0] = UInt8(config.reportId)
        var reportLength = report.count

        let readResult = report.withUnsafeMutableBufferPointer { pointer in
            IOHIDDeviceGetReport(
                device,
                kIOHIDReportTypeFeature,
                CFIndex(config.reportId),
                pointer.baseAddress!,
                &reportLength
            )
        }
        guard readResult == kIOReturnSuccess else {
            throw HidCommandError.readFailed(readResult)
        }

        let response = decodeReport(Array(report.prefix(reportLength)))
        guard !response.isEmpty else {
            throw HidCommandError.emptyResponse
        }

        return response
    }

    private func isAcceptedResponse(_ response: String) -> Bool {
        response == "PONG"
            || response.hasPrefix("OK ")
            || response.hasPrefix("STATUS ")
            || response.hasPrefix("COMMANDS ")
            || response.hasPrefix("ERROR ")
    }

    private func decodeReport(_ report: [UInt8]) -> String {
        guard !report.isEmpty else {
            return ""
        }

        let cursor = report[0] == UInt8(config.reportId) ? 1 : 0
        guard report.count > cursor else {
            return ""
        }

        let length = Int(report[cursor])
        let start = cursor + 1
        let end = min(start + length, report.count)
        guard length > 0, end > start else {
            return ""
        }

        return String(decoding: report[start..<end], as: UTF8.self)
    }

    private func propertyString(_ device: IOHIDDevice, _ key: String) -> String? {
        IOHIDDeviceGetProperty(device, key as CFString) as? String
    }
}

func environment(_ key: String, default defaultValue: String) -> String {
    let value = ProcessInfo.processInfo.environment[key] ?? ""
    return value.isEmpty ? defaultValue : value
}

func environmentInt(_ key: String, default defaultValue: Int) -> Int {
    let rawValue = environment(key, default: "")
    if rawValue.hasPrefix("0x") || rawValue.hasPrefix("0X") {
        return Int(rawValue.dropFirst(2), radix: 16) ?? defaultValue
    }

    return Int(rawValue) ?? defaultValue
}

func describe(_ error: Error) -> String {
    switch error {
    case HidCommandError.deviceNotConnected:
        return "SKIP BLE_NOT_CONNECTED"
    case HidCommandError.commandTooLong(let maxLength):
        return "ERROR HID_COMMAND_TOO_LONG max=\(maxLength)"
    case HidCommandError.openFailed(let code):
        return "ERROR HID_OPEN_FAILED code=\(code)"
    case HidCommandError.writeFailed(let code):
        return "ERROR HID_WRITE_FAILED code=\(code)"
    case HidCommandError.readFailed(let code):
        return "ERROR HID_READ_FAILED code=\(code)"
    case HidCommandError.emptyResponse:
        return "ERROR HID_EMPTY_RESPONSE"
    case HidCommandError.invalidResponse(let response):
        return "ERROR HID_INVALID_RESPONSE response=\(response)"
    default:
        return "ERROR \(error.localizedDescription)"
    }
}

let arguments = CommandLine.arguments.dropFirst()
guard let command = arguments.first?.trimmingCharacters(in: .whitespacesAndNewlines), !command.isEmpty else {
    fputs("Usage: AgentLightBluetoothHelper <STATE>\n", stderr)
    exit(2)
}

let config = HidCommandConfig(
    deviceName: environment("AGENTLIGHT_BLE_DEVICE_NAME", default: "WHALESKY-LABS-AGENTLIGHT"),
    usagePage: environmentInt("AGENTLIGHT_HID_USAGE_PAGE", default: 0xFF00),
    usage: environmentInt("AGENTLIGHT_HID_USAGE", default: 0x0001),
    reportId: environmentInt("AGENTLIGHT_HID_REPORT_ID", default: 1),
    reportSize: environmentInt("AGENTLIGHT_HID_REPORT_SIZE", default: 32)
)

do {
    print(try SystemBluetoothHidCommand(config: config, command: command).run())
    exit(0)
} catch {
    let message = describe(error)
    print(message)
    exit(message.hasPrefix("SKIP ") ? 0 : 1)
}
