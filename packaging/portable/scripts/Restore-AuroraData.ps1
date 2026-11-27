param([Parameter(Mandatory=$true)][string]$BackupZip)
$ErrorActionPreference='Stop'
if ((Read-Host 'Restore will replace matching data files. Type RESTORE to continue') -cne 'RESTORE') { throw 'Restore cancelled.' }
$backup=Resolve-Path $BackupZip
$checksumFile="$($backup.Path).sha256"
if (-not (Test-Path $checksumFile)) { throw 'Backup SHA-256 sidecar is missing.' }
$expected=(Get-Content -LiteralPath $checksumFile -Raw).Trim().Split(' ')[0]
$actual=(Get-FileHash -LiteralPath $backup.Path -Algorithm SHA256).Hash.ToLower()
if ($expected -notmatch '^[0-9a-f]{64}$' -or $actual -ne $expected) { throw 'Backup checksum is invalid.' }
$data=Join-Path $env:LOCALAPPDATA 'Aurora'
& (Join-Path $PSScriptRoot 'Backup-AuroraData.ps1')
$temp=Join-Path $env:TEMP ([guid]::NewGuid().ToString()); New-Item -ItemType Directory $temp | Out-Null
try {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zip=[IO.Compression.ZipFile]::OpenRead($backup.Path)
  try {
    foreach($entry in $zip.Entries) {
      $name=$entry.FullName.Replace('\','/')
      if ([IO.Path]::IsPathRooted($name) -or $name.Contains(':') -or ($name -split '/') -contains '..') { throw "Unsafe backup path: $name" }
    }
  } finally { $zip.Dispose() }
  Expand-Archive -LiteralPath $backup -DestinationPath $temp
  foreach($name in 'config','database','conversations','faiss_index','documents','logs') { $source=Join-Path $temp $name; if(Test-Path $source){Copy-Item $source $data -Recurse -Force} }
} finally { Remove-Item $temp -Recurse -Force }
