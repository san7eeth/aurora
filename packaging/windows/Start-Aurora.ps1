$ErrorActionPreference = 'Stop'
$exePath = Join-Path $PSScriptRoot 'Aurora.exe'
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Aurora.exe was not found at $exePath"
}

$healthUrl = 'http://127.0.0.1:8000/health'
try {
    $existing = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
    if ($existing) {
        Start-Process $healthUrl
        Write-Output 'Aurora is already running.'
        exit 0
    }
} catch { }

Start-Process -FilePath $exePath -WindowStyle Hidden
$ready = $false
for ($attempt = 0; $attempt -lt 120; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
        if ($health.status -in @('ok', 'degraded')) { $ready = $true; break }
    } catch { }
}

if (-not $ready) {
    $logPath = Join-Path $env:LOCALAPPDATA 'Aurora\logs\aurora.log'
    throw "Aurora did not become ready within 60 seconds. Check $logPath"
}

Start-Process 'http://127.0.0.1:8000/'
Write-Output 'Aurora is ready at http://127.0.0.1:8000/'
