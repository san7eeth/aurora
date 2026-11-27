<#
.SYNOPSIS
  Clean-VM validation for the Aurora portable ZIP.

.DESCRIPTION
  Run on a clean Windows 10/11 x64 VM (no Python/Node) with the release ZIP and the
  independently published signing-key fingerprint. Writes a results file next to the script.

  ASSUMPTIONS TO CHECK (not visible to the author of this script):
    * Aurora.exe supports --self-check, --port and --data-dir.
    * The verifier executable's command line matches -VerifierArgs (adjust the template).
    * /health returns JSON containing a database status.
  Anything this script cannot automate is listed as MANUAL in the results.

.EXAMPLE
  .\Test-PortableRelease.ps1 -ZipPath C:\t\Aurora-v1.0.0-Windows-x64-Portable.zip `
      -TrustedFingerprint <sha256-hex> -VerifierExe C:\t\verify\AuroraReleaseVerifier.exe `
      -PublicKeyPath C:\t\verify\release_public_key.pem
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ZipPath,
    [Parameter(Mandatory)][string]$TrustedFingerprint,
    [Parameter(Mandatory)][string]$VerifierExe,
    [Parameter(Mandatory)][string]$PublicKeyPath,
    # Placeholders: {zip}, {key} and {fp} match the bundled verifier CLI.
    [string]$VerifierArgs = '--zip "{zip}" --public-key "{key}" --fingerprint {fp}',
    [int]$Port = 8000,
    [int]$ObserveSeconds = 60,
    [string]$WorkDir = 'C:\ar',
    [switch]$ExpectOffline
)

$ErrorActionPreference = 'Continue'
$results = New-Object System.Collections.Generic.List[object]
$started = Get-Date

function Record([string]$Name, [string]$Status, [string]$Detail = '') {
    $results.Add([pscustomobject]@{ Test = $Name; Status = $Status; Detail = $Detail })
    $color = switch ($Status) { 'PASS' {'Green'} 'FAIL' {'Red'} 'WARN' {'Yellow'} default {'Cyan'} }
    Write-Host ("[{0}] {1} {2}" -f $Status, $Name, $Detail) -ForegroundColor $color
}

function Invoke-Verifier([string]$Zip, [string]$Fingerprint) {
    $argLine = $VerifierArgs.Replace('{zip}', $Zip).Replace('{key}', $PublicKeyPath).Replace('{fp}', $Fingerprint)
    $p = Start-Process -FilePath $VerifierExe -ArgumentList $argLine -Wait -PassThru -NoNewWindow `
        -RedirectStandardOutput "$WorkDir\v.out" -RedirectStandardError "$WorkDir\v.err"
    return $p.ExitCode
}

function Expand-To([string]$Zip, [string]$Dest) {
    if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force }
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($Zip, $Dest)
}

function Find-AuroraExe([string]$Root) {
    Get-ChildItem -Path $Root -Filter 'Aurora.exe' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
}

# ---- Environment ----
$WorkDir = [IO.Path]::GetFullPath($WorkDir)
$driveRoot = [IO.Path]::GetPathRoot($WorkDir)
if ($WorkDir.TrimEnd('\').Equals($driveRoot.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'WorkDir cannot be a drive root.'
}
if (Test-Path -LiteralPath $WorkDir) {
    throw "WorkDir must be a new, non-existing directory to protect existing files: $WorkDir"
}
New-Item -ItemType Directory -Path $WorkDir | Out-Null
$os = Get-CimInstance Win32_OperatingSystem
Record 'Environment' 'INFO' ("{0} build {1}, {2}" -f $os.Caption, $os.BuildNumber, $os.OSArchitecture)
if ($os.OSArchitecture -notmatch '64') { Record 'x64 OS' 'FAIL' $os.OSArchitecture }

$py = Get-Command python, py -ErrorAction SilentlyContinue
if ($py) { Record 'No Python on PATH' 'WARN' 'Python found; this VM is not clean' } else { Record 'No Python on PATH' 'PASS' }

$online = $false
try { $online = (Test-NetConnection -ComputerName '1.1.1.1' -Port 443 -WarningAction SilentlyContinue).TcpTestSucceeded } catch {}
if ($ExpectOffline -and $online) { Record 'Offline state' 'FAIL' 'Internet reachable but -ExpectOffline was set' }
elseif ($ExpectOffline) { Record 'Offline state' 'PASS' 'No internet' }
else { Record 'Network state' 'INFO' ("internet reachable: $online") }

# ---- Signature and tamper tests ----
if (-not (Test-Path $ZipPath)) { Record 'ZIP present' 'FAIL' $ZipPath; return }
if (-not (Test-Path $VerifierExe)) { Record 'Verifier present' 'FAIL' $VerifierExe; return }
if (-not (Test-Path $PublicKeyPath)) { Record 'Public key present' 'FAIL' $PublicKeyPath; return }

$code = Invoke-Verifier $ZipPath $TrustedFingerprint
Record 'Valid ZIP verifies with pinned fingerprint' ($(if ($code -eq 0) {'PASS'} else {'FAIL'})) "exit $code"

$wrongFp = ('0' * 64)
$code = Invoke-Verifier $ZipPath $wrongFp
Record 'Wrong fingerprint rejected' ($(if ($code -ne 0) {'PASS'} else {'FAIL'})) "exit $code"

# Unlisted file inside the expected Aurora/ package root
$extra = "$WorkDir\extra.zip"
Copy-Item $ZipPath $extra -Force
Add-Type -AssemblyName System.IO.Compression
$fs = [IO.File]::Open($extra, 'Open', 'ReadWrite')
$za = New-Object IO.Compression.ZipArchive($fs, [IO.Compression.ZipArchiveMode]::Update)
$e = $za.CreateEntry('Aurora/unlisted-extra.txt'); $w = New-Object IO.StreamWriter($e.Open()); $w.Write('x'); $w.Dispose()
$za.Dispose(); $fs.Dispose()
$code = Invoke-Verifier $extra $TrustedFingerprint
Record 'ZIP with unlisted file rejected' ($(if ($code -ne 0) {'PASS'} else {'FAIL'})) "exit $code"

# Modified payload: rewrite the VERSION entry with different content
$mod = "$WorkDir\modified.zip"
Copy-Item $ZipPath $mod -Force
$fs = [IO.File]::Open($mod, 'Open', 'ReadWrite')
$za = New-Object IO.Compression.ZipArchive($fs, [IO.Compression.ZipArchiveMode]::Update)
$target = $za.Entries | Where-Object { $_.Name -eq 'VERSION' } | Select-Object -First 1
if ($target) {
    $name = $target.FullName; $target.Delete()
    $e = $za.CreateEntry($name); $w = New-Object IO.StreamWriter($e.Open()); $w.Write('9.9.9-tampered'); $w.Dispose()
}
$za.Dispose(); $fs.Dispose()
if ($target) {
    $code = Invoke-Verifier $mod $TrustedFingerprint
    Record 'Modified payload rejected' ($(if ($code -ne 0) {'PASS'} else {'FAIL'})) "exit $code"
} else { Record 'Modified payload rejected' 'SKIP' 'No VERSION entry found to modify' }

Remove-Item $extra, $mod -Force -ErrorAction SilentlyContinue

# ---- Extract: normal path ----
$normal = "$WorkDir\n"
Expand-To $ZipPath $normal
$exe = Find-AuroraExe $normal
if (-not $exe) { Record 'Aurora.exe found after extract' 'FAIL'; return }
Record 'Aurora.exe found after extract' 'PASS' $exe.FullName

$allFiles = Get-ChildItem -LiteralPath $normal -Recurse -File
$forbidden = $allFiles | Where-Object {
    $_.Extension -in @('.py', '.pyc', '.pyo', '.pyi') -or
    $_.Name -eq '.env' -or
    $_.FullName -match '[\\/]\.git[\\/]' -or
    $_.Name -match '(^|[-_])(private[-_]?key|credential|test[-_]?credential)([-_.]|$)'
}
Record 'No source, credentials or Git metadata distributed' ($(if ($forbidden) {'FAIL'} else {'PASS'})) (($forbidden.FullName | Select-Object -First 5) -join ',')
Record 'Portable package directory structure' ($(if (
    (Test-Path "$normal\Aurora\runtime") -and
    (Test-Path "$normal\Aurora\resources") -and
    (Test-Path "$normal\Aurora\frontend") -and
    (Test-Path "$normal\Aurora\scripts") -and
    (Test-Path "$normal\Aurora\Start Aurora.exe") -and
    (Test-Path "$normal\Aurora\SHA256SUMS.txt")
) {'PASS'} else {'FAIL'})) 'Expected Aurora/ runtime/resources/frontend/scripts layout'

# ---- Self-check ----
$p = Start-Process -FilePath $exe.FullName -ArgumentList '--self-check' -Wait -PassThru -NoNewWindow
Record 'Self-check (short path)' ($(if ($p.ExitCode -eq 0) {'PASS'} else {'FAIL'})) "exit $($p.ExitCode)"

# ---- Extract: deep path (MAX_PATH regression) ----
$deep = "$WorkDir\" + (('deepfolder_' * 12).TrimEnd('_')) + '\extracted'
try {
    Expand-To $ZipPath $deep
    $deepExe = Find-AuroraExe $deep
    $p = Start-Process -FilePath $deepExe.FullName -ArgumentList '--self-check' -Wait -PassThru -NoNewWindow
    Record 'Self-check (deep path)' ($(if ($p.ExitCode -eq 0) {'PASS'} else {'FAIL'})) "exit $($p.ExitCode); path length $($deepExe.FullName.Length)"
} catch { Record 'Self-check (deep path)' 'FAIL' $_.Exception.Message }

# ---- Run the app ----
$dataDir = "$WorkDir\data"
if (Test-Path $dataDir) { Remove-Item $dataDir -Recurse -Force }
$proc = Start-Process -FilePath $exe.FullName -ArgumentList "--port $Port --data-dir `"$dataDir`"" -PassThru -WindowStyle Hidden
$health = $null
for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 2
    try { $health = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 3; break } catch {}
    if ($proc.HasExited) { break }
}
if ($health) {
    Record '/health reachable' 'PASS' ($health | ConvertTo-Json -Compress)
    $dbOk = ($health | ConvertTo-Json -Compress) -match '"database"\s*:\s*"?ok'
    Record 'Database status ok' ($(if ($dbOk) {'PASS'} else {'WARN'})) 'Check /health output above'
} else {
    Record '/health reachable' 'FAIL' ("process exited: " + $proc.HasExited)
}

try { $ui = Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 5; Record 'Frontend served' ($(if ($ui.StatusCode -eq 200) {'PASS'} else {'FAIL'})) "HTTP $($ui.StatusCode)" }
catch { Record 'Frontend served' 'FAIL' $_.Exception.Message }

# ---- Bind address: must not listen on 0.0.0.0 / :: ----
$listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if ($listeners) {
    $bad = $listeners | Where-Object { $_.LocalAddress -notin @('127.0.0.1', '::1') }
    Record 'Listens on loopback only' ($(if ($bad) {'FAIL'} else {'PASS'})) (($listeners.LocalAddress | Sort-Object -Unique) -join ',')
} else { Record 'Listens on loopback only' 'FAIL' 'No listener found' }

# ---- Data layout ----
$dirs = Get-ChildItem $dataDir -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
Record 'Data directory created' ($(if ($dirs) {'PASS'} else {'FAIL'})) ("found: " + ($dirs -join ', '))

# ---- Outbound connection observation ----
$ids = @($proc.Id) + (Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $proc.Id } | ForEach-Object ProcessId)
$seen = New-Object System.Collections.Generic.HashSet[string]
$end = (Get-Date).AddSeconds($ObserveSeconds)
while ((Get-Date) -lt $end) {
    Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $ids -contains $_.OwningProcess } | ForEach-Object {
        if ($_.RemoteAddress -notin @('127.0.0.1', '::1', '0.0.0.0', '::')) { [void]$seen.Add("$($_.RemoteAddress):$($_.RemotePort)") }
    }
    Start-Sleep -Seconds 1
}
if ($seen.Count -eq 0) { Record "No non-loopback connections ($ObserveSeconds s)" 'PASS' 'Trigger chat/upload/voice manually during this window for a stronger result' }
else { Record "No non-loopback connections ($ObserveSeconds s)" 'FAIL' (($seen | Sort-Object) -join ', ') }

# ---- Shutdown ----
if (-not $proc.HasExited) {
    & $exe.FullName --shutdown
    Start-Sleep -Seconds 2
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}

# ---- Manual items ----
$manual = @(
    'FastAPI and frontend work after process restart; test REST health and chat',
    'Native WebSocket chat and voice endpoints work; app uses FastAPI WebSockets, not Socket.IO',
    'Ollama missing: launcher displays local setup instructions and still offers to start',
    'Ollama available with configured model: local inference succeeds',
    'Ollama available without configured model: launcher displays model pull instructions',
    'FAISS/RAG: ingest a document, restart Aurora, and retrieve relevant content',
    'Voice: microphone input and offline TTS work; test FFmpeg-dependent audio decode if enabled',
    'Persistence: conversations/config survive a restart and an application update',
    'Offline: disconnect network, use cached models, and verify core local assistant behavior',
    'Update: valid signed online and manually imported ZIPs require confirmation and preserve user data',
    'Integrity: unsigned, invalid-signature, wrong-fingerprint and modified ZIPs are rejected before extraction',
    'Rollback: simulate failed new-version self-check and restore the previous application version',
    'User-controlled export/backup and restore work on a separate fresh data directory',
    'No cloud AI calls or telemetry; review observed connections while exercising app features',
    'Graceful stop via packaged stop script or Aurora.exe --shutdown',
    'SmartScreen / Defender behavior noted'
)
foreach ($m in $manual) { Record $m 'MANUAL' }

# ---- Write results ----
$out = Join-Path $PSScriptRoot ("portable-validation-{0:yyyyMMdd-HHmmss}.md" -f $started)
$lines = @(
    '# Aurora portable validation results', '',
    "Date: $started", "OS: $($os.Caption) build $($os.BuildNumber) $($os.OSArchitecture)",
    "ZIP: $ZipPath", "SHA256: $((Get-FileHash $ZipPath -Algorithm SHA256).Hash)", '',
    '| Test | Status | Detail |', '|---|---|---|'
)
$lines += $results | ForEach-Object { "| $($_.Test) | $($_.Status) | $($_.Detail -replace '\|','/') |" }
$lines | Set-Content -Path $out -Encoding UTF8
Write-Host "`nResults written to $out"

$fails = ($results | Where-Object Status -eq 'FAIL').Count
Write-Host ("FAIL: {0}  MANUAL: {1}" -f $fails, ($results | Where-Object Status -eq 'MANUAL').Count)
if ($fails -gt 0) { exit 1 } else { exit 0 }
