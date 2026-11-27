$ErrorActionPreference='Stop'
$data=Join-Path $env:LOCALAPPDATA 'Aurora'
if (-not (Test-Path $data)) { throw "No Aurora data directory: $data" }
$runningApp=Join-Path (Split-Path $PSScriptRoot -Parent) 'Aurora.exe'
if (Test-Path $runningApp) { & $runningApp --shutdown; if ($LASTEXITCODE) { throw 'Aurora did not shut down cleanly; backup aborted.' } }
$target=Join-Path $data ("backups\user-data-{0}.zip" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
$temp=Join-Path $env:TEMP ([guid]::NewGuid().ToString())
New-Item -ItemType Directory $temp | Out-Null
try {
  foreach($name in 'config','database','conversations','faiss_index','documents','logs') { $source=Join-Path $data $name; if(Test-Path $source){Copy-Item $source $temp -Recurse} }
  Compress-Archive -Path (Join-Path $temp '*') -DestinationPath $target
  $hash=(Get-FileHash $target -Algorithm SHA256).Hash.ToLower()
  "$hash  $(Split-Path $target -Leaf)" | Set-Content -LiteralPath "$target.sha256" -Encoding ascii
  Write-Host "Backup created: $target"
} finally { Remove-Item $temp -Recurse -Force }
