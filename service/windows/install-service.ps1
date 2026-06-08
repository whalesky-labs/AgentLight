<#
This file is part of AgentLight.

@link     https://github.com/whalesky-labs/AgentLight
@document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
@contact  root@imoi.cn
@license  https://github.com/whalesky-labs/AgentLight
#>

param(
    [string]$ServiceName = "whalesky-labs-AgentLight",
    [string]$DisplayName = "WhaleSky Labs AgentLight",
    [string]$PythonPath = "python",
    [string]$RepoRoot = "",
    [string]$ConfigPath = "$env:ProgramData\whalesky-labs-AgentLight\agentlight-agent.json"
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Please run PowerShell as Administrator."
    }
}

Assert-Administrator

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
} else {
    $RepoRoot = Resolve-Path $RepoRoot
}

$agentScript = Join-Path $RepoRoot "scripts\agentlight-agent"
$configTemplate = Join-Path $RepoRoot "config\agentlight-agent.example.json"
$programData = Join-Path $env:ProgramData "whalesky-labs-AgentLight"
$logDir = Join-Path $programData "logs"

New-Item -ItemType Directory -Path $programData -Force | Out-Null
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

if (-not (Test-Path $ConfigPath)) {
    Copy-Item $configTemplate $ConfigPath
}

$pythonCommand = (Get-Command $PythonPath).Source
$binaryPath = "`"$pythonCommand`" `"$agentScript`" run --config `"$ConfigPath`""

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    sc.exe stop $ServiceName | Out-Null
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

sc.exe create $ServiceName binPath= $binaryPath start= auto DisplayName= $DisplayName | Out-Null
sc.exe description $ServiceName "WhaleSky Labs AgentLight background service for AI Agent status light synchronization." | Out-Null
sc.exe failure $ServiceName reset= 60 actions= restart/5000/restart/5000/restart/5000 | Out-Null

Start-Service -Name $ServiceName

Write-Host "Installed and started $ServiceName"
Write-Host "Config: $ConfigPath"
Write-Host "Logs: $logDir"
