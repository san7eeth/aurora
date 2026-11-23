$ErrorActionPreference = 'Stop'
$exePath = Join-Path $PSScriptRoot 'Aurora.exe'
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Aurora.exe was not found at $exePath"
}

$shutdown = Start-Process -FilePath $exePath -ArgumentList '--shutdown' -WindowStyle Hidden -PassThru -Wait
if ($shutdown.ExitCode -ne 0) {
    throw "Aurora did not stop cleanly (exit code $($shutdown.ExitCode))."
}
Write-Output 'Aurora stop request completed.'
