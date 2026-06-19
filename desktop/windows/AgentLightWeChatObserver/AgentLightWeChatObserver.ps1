<#
This file is part of AgentLight.

@link     https://github.com/whalesky-labs/AgentLight
@document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
@contact  root@imoi.cn
@license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#>

param(
    [switch]$Once
)

$ErrorActionPreference = "Stop"

function New-WeChatPayload {
    param(
        [string]$Event,
        [string]$Conversation = "",
        [string]$Sender = "",
        [string]$Summary = "",
        [string]$Confidence = "unread-only",
        [string]$Diagnostic = "",
        [string[]]$Capabilities = @()
    )

    [ordered]@{
        source = "wechat"
        event = $Event
        platform = "windows"
        conversation = $Conversation
        sender = $Sender
        summary = $Summary
        confidence = $Confidence
        diagnostic = $Diagnostic
        capabilities = $Capabilities
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    } | ConvertTo-Json -Compress
}

function Get-WeChatProcess {
    Get-Process | Where-Object {
        $_.ProcessName -match "WeChat|Weixin|微信"
    } | Select-Object -First 1
}

$process = Get-WeChatProcess
if (-not $process) {
    New-WeChatPayload -Event "wechat-offline" -Confidence "diagnostic" -Diagnostic "WeChat process is not running"
    exit 0
}

try {
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $condition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty,
        $process.Id
    )
    $window = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $condition)
    $title = ""
    if ($window) {
        $title = $window.Current.Name
    }
    $texts = @()
    if ($window) {
        $conditionAll = [System.Windows.Automation.Condition]::TrueCondition
        $items = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $conditionAll)
        $limit = [Math]::Min($items.Count, 200)
        for ($index = 0; $index -lt $limit; $index++) {
            $name = $items.Item($index).Current.Name
            if (-not [string]::IsNullOrWhiteSpace($name)) {
                $texts += $name
            }
        }
    }
    $signal = $texts | Where-Object {
        $_ -match "未读|条新消息|有人@我|@我|new message|unread"
    } | Select-Object -First 1

    if ($signal) {
        New-WeChatPayload -Event "wechat-message" -Conversation $title -Summary $signal -Confidence "visible-summary" -Capabilities @("process-running", "ui-automation", "visible-summary")
    } else {
        New-WeChatPayload -Event "wechat-cleared" -Conversation $title -Confidence "conversation-title" -Capabilities @("process-running", "ui-automation", "conversation-title")
    }
    exit 0
} catch {
    New-WeChatPayload -Event "wechat-listener-error" -Confidence "diagnostic" -Diagnostic "UI Automation failed: $($_.Exception.Message)" -Capabilities @("process-running")
    exit 0
}
