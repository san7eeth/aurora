param([string]$PackagePath,[Parameter(Mandatory=$true)][string]$Fingerprint)
$ErrorActionPreference='Stop'
$app=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$data=Join-Path $env:LOCALAPPDATA 'Aurora'
$releaseNotes=''
if (-not $PackagePath) {
  $release=Invoke-RestMethod -Headers @{ 'User-Agent'='Aurora-Updater' } -Uri 'https://api.github.com/repos/san7eeth/aurora/releases/latest'
  $asset=$release.assets | Where-Object name -Match '^Aurora-v\d+\.\d+\.\d+-Windows-x64-Portable\.zip$' | Select-Object -First 1
  if (-not $asset) { throw 'Official release has no portable ZIP asset.' }
  $assetUri=[uri]$asset.browser_download_url
  if ($assetUri.Scheme -ne 'https' -or $assetUri.Host -ne 'github.com' -or -not $assetUri.AbsolutePath.StartsWith('/san7eeth/aurora/releases/download/',[StringComparison]::Ordinal)) { throw 'Release asset URL is outside the official Aurora GitHub release path.' }
  $PackagePath=Join-Path $env:TEMP $asset.name
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $PackagePath
}
& (Join-Path $PSScriptRoot 'Verify-Release.ps1') -PackagePath $PackagePath -Fingerprint $Fingerprint
if ($LASTEXITCODE -ne 0) { throw 'Release signature or hashes failed; update aborted.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $PackagePath).Path)
try {
  $entry=$zip.GetEntry('Aurora/release_manifest.json')
  if (-not $entry) { throw 'Verified package is missing its release manifest.' }
  $reader=New-Object IO.StreamReader($entry.Open())
  try { $releaseNotes=([string](ConvertFrom-Json -InputObject $reader.ReadToEnd()).release_notes) }
  finally { $reader.Dispose() }
} finally { $zip.Dispose() }
Write-Host "Release notes:`n$releaseNotes"
if ((Read-Host 'Verified update. Install now? Type UPDATE to continue') -cne 'UPDATE') { throw 'Update cancelled.' }
$backup=Join-Path $data ("backups\portable-app-{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force $backup | Out-Null
$staging=Join-Path $env:TEMP ([guid]::NewGuid().ToString()); New-Item -ItemType Directory $staging | Out-Null
$new=Join-Path $staging 'new'; Expand-Archive -LiteralPath $PackagePath -DestinationPath $new
$top=Join-Path $new 'Aurora'
if (-not (Test-Path (Join-Path $top 'Aurora.exe')) -or -not (Test-Path (Join-Path $top 'runtime'))) { throw 'Unexpected portable ZIP layout.' }
$previous=Join-Path $staging 'previous'
try {
  $currentExe=Join-Path $app 'Aurora.exe'
  if (Test-Path $currentExe) { & $currentExe --shutdown; if ($LASTEXITCODE) { throw 'Aurora did not stop cleanly; update aborted.' } }
  Get-ChildItem $app -Force | Where-Object Name -ne 'scripts' | Copy-Item -Destination $backup -Recurse -Force
  foreach($item in Get-ChildItem $app -Force) { if($item.Name -ne 'scripts'){Remove-Item $item.FullName -Recurse -Force} }
  Copy-Item (Join-Path $top '*') $app -Recurse -Force
  & (Join-Path $app 'Aurora.exe') --self-check
  if ($LASTEXITCODE) { throw 'New application self-check failed.' }
} catch {
  foreach($item in Get-ChildItem $app -Force) { if($item.Name -ne 'scripts'){Remove-Item $item.FullName -Recurse -Force} }
  Copy-Item (Join-Path $backup '*') $app -Recurse -Force
  throw
} finally { Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "Update complete; previous app backed up to $backup"
