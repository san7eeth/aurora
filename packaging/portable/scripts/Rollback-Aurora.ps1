param([Parameter(Mandatory=$true)][string]$BackupPath)
$ErrorActionPreference='Stop'
$app=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backup=(Resolve-Path $BackupPath).Path
if ((Read-Host "Restore previous application from $backup? Type ROLLBACK") -cne 'ROLLBACK') { throw 'Rollback cancelled.' }
$currentExe=Join-Path $app 'Aurora.exe'
if (Test-Path $currentExe) { & $currentExe --shutdown; if ($LASTEXITCODE) { throw 'Aurora did not stop cleanly; rollback aborted.' } }
$current=Join-Path $env:TEMP ([guid]::NewGuid().ToString()); New-Item -ItemType Directory $current | Out-Null
try {
  Get-ChildItem $app -Force | Where-Object Name -ne 'scripts' | Copy-Item -Destination $current -Recurse -Force
  foreach($item in Get-ChildItem $app -Force) { if($item.Name -ne 'scripts'){Remove-Item $item.FullName -Recurse -Force} }
  Copy-Item (Join-Path $backup '*') $app -Recurse -Force
  & (Join-Path $app 'Aurora.exe') --self-check
  if ($LASTEXITCODE) { throw 'Restored application failed self-check.' }
} catch {
  foreach($item in Get-ChildItem $app -Force) { if($item.Name -ne 'scripts'){Remove-Item $item.FullName -Recurse -Force} }
  Copy-Item (Join-Path $current '*') $app -Recurse -Force
  throw
} finally { Remove-Item $current -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host 'Rollback completed.'
