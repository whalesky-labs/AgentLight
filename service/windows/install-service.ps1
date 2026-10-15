<#
This file is part of AgentLight.

@link     https://github.com/whalesky-labs/AgentLight
@document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
@contact  root@imoi.cn
@license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
#>

param(
    [string]$ServiceName = "whalesky-labs-AgentLight",
    [string]$DisplayName = "WhaleSky Labs AgentLight",
    [string]$PythonPath = "python",
    [string]$RepoRoot = "",
    [string]$ConfigPath = "$env:ProgramData\whalesky-labs-AgentLight\agentlight-agent.json",
    [string]$BashPath = "$env:ProgramFiles\Git\bin\bash.exe",
    [string]$UserProfilePath = "$env:USERPROFILE"
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
$ConfigPath = [System.IO.Path]::GetFullPath($ConfigPath)

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
} else {
    $RepoRoot = Resolve-Path $RepoRoot
}

$serviceScript = Join-Path $RepoRoot "service\windows\agentlight_service.py"
$configTemplate = Join-Path $RepoRoot "config\agentlight-agent.example.json"
$programData = Join-Path $env:ProgramData "whalesky-labs-AgentLight"
$logDir = Join-Path $programData "logs"
$venvDir = Join-Path $RepoRoot ".venv-agent"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$requirements = Join-Path $RepoRoot "requirements.txt"

New-Item -ItemType Directory -Path $programData -Force | Out-Null
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path -Parent $ConfigPath) -Force | Out-Null

if (-not (Test-Path $BashPath)) {
    throw "Git Bash is required. Install Git for Windows or supply -BashPath."
}

if (-not (Test-Path $ConfigPath)) {
    Copy-Item $configTemplate $ConfigPath
}

$pythonCommand = (Get-Command $PythonPath).Source

if (-not (Test-Path $venvPython)) {
    & $pythonCommand -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Pip upgrade failed." }
}

& $venvPython -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

$config = Get-Content -Raw -Encoding UTF8 $ConfigPath | ConvertFrom-Json
$config.environment | Add-Member -NotePropertyName AGENTLIGHT_BASH -NotePropertyValue ($BashPath -replace '\\', '/') -Force
if (-not $config.environment.AGENTLIGHT_STATE_DIR) {
    $config.environment | Add-Member -NotePropertyName AGENTLIGHT_STATE_DIR -NotePropertyValue (Join-Path $programData "state") -Force
}
if ([string]::IsNullOrWhiteSpace($config.logFile)) {
    $config | Add-Member -NotePropertyName logFile -NotePropertyValue (Join-Path $logDir "agentlight-agent.log") -Force
}
$json = $config | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($ConfigPath, $json, (New-Object System.Text.UTF8Encoding($false)))

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
    (Get-Service -Name $ServiceName).WaitForStatus("Stopped", [TimeSpan]::FromSeconds(20))
    $serviceAction = "update"
} else {
    $serviceAction = "install"
}

& $venvPython $serviceScript --service-name $ServiceName --display-name $DisplayName --startup auto `
    --config $ConfigPath --repo "$RepoRoot" --python $venvPython --user-profile $UserProfilePath $serviceAction
if ($LASTEXITCODE -ne 0) { throw "Windows service registration failed." }
sc.exe failure $ServiceName reset= 60 actions= restart/5000/restart/5000/restart/5000 | Out-Null

Start-Service -Name $ServiceName

Write-Host "Installed and started $ServiceName"
Write-Host "Config: $ConfigPath"
Write-Host "Logs: $logDir"
