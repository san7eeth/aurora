param(
  [string]$Version,
  [switch]$UnsignedCandidate,
  [string]$OutputRoot,
  [string]$DistributionPath,
  [string]$ToolsDirectory,
  [string]$PrivateKey=$env:AURORA_RELEASE_PRIVATE_KEY,
  [string]$PublicKey=$env:AURORA_RELEASE_PUBLIC_KEY,
  [string]$ExpectedFingerprint=$env:AURORA_RELEASE_KEY_FINGERPRINT
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $Version) { $Version=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'VERSION') -Raw).Trim() }
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Version must use semantic version form MAJOR.MINOR.PATCH.' }
$python=Join-Path $root 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Python 3.12 build environment is missing.' }

$commit = (& git -C $root rev-parse --short=12 HEAD 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $commit) { throw 'A release must be built from a Git commit.' }
$changes = (& git -C $root status --porcelain --untracked-files=all)
if ($LASTEXITCODE -ne 0) { throw 'Could not verify the Git worktree state.' }
if ($changes) { throw 'Commit all intended source changes and resolve unrelated changes before packaging.' }

if (-not $UnsignedCandidate) {
  if (-not $PrivateKey -or -not $PublicKey -or -not $ExpectedFingerprint) { throw 'Set external private/public key paths and independently trusted AURORA_RELEASE_KEY_FINGERPRINT.' }
  foreach ($key in @($PrivateKey,$PublicKey)) {
    if (-not (Test-Path -LiteralPath $key -PathType Leaf)) { throw "Key file not found: $key" }
    $resolvedKey=(Resolve-Path -LiteralPath $key).Path
    if ($resolvedKey.Equals($root,[StringComparison]::OrdinalIgnoreCase) -or $resolvedKey.StartsWith($root.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Signing keys must stay outside the repository.' }
  }
  $env:AURORA_RELEASE_PRIVATE_KEY = $PrivateKey
  $env:AURORA_RELEASE_PUBLIC_KEY = $PublicKey
  $env:AURORA_RELEASE_KEY_FINGERPRINT = $ExpectedFingerprint
  & $python -c "import os,sys;sys.dont_write_bytecode=True;sys.path.insert(0,r'$PSScriptRoot');from release_security import validate_signing_keys;validate_signing_keys(os.environ['AURORA_RELEASE_PRIVATE_KEY'],os.environ['AURORA_RELEASE_PUBLIC_KEY'],os.environ['AURORA_RELEASE_KEY_FINGERPRINT'])"
  if ($LASTEXITCODE) { throw 'Signing key pair or trusted fingerprint validation failed.' }
}

$releaseRoot = if ($OutputRoot) { [IO.Path]::GetFullPath($OutputRoot) } else { Join-Path $root 'release' }
if ($OutputRoot -and (Test-Path -LiteralPath $releaseRoot)) { throw "Refusing to overwrite existing output root: $releaseRoot" }
New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null
$suffix = if ($UnsignedCandidate) { '-UNSIGNED-RC' } else { '' }
$stagingRoot=Join-Path $releaseRoot "Aurora-v$Version-Windows-x64-Portable$suffix"
$staging=Join-Path $stagingRoot 'Aurora'
$zip=Join-Path $releaseRoot "Aurora-v$Version-Windows-x64-Portable$suffix.zip"
$zipTemp=Join-Path $stagingRoot "Aurora-v$Version-Windows-x64-Portable$suffix.candidate.zip"
if (Test-Path $stagingRoot) { throw "Candidate staging already exists; preserve and inspect it before choosing another version: $stagingRoot" }
if (Test-Path $zip) { throw "Release ZIP already exists; refusing to overwrite: $zip" }
if (Test-Path "$zip.sha256") { throw "Release checksum already exists; refusing to overwrite: $zip.sha256" }
$dist = if ($DistributionPath) { [IO.Path]::GetFullPath($DistributionPath) } else { Join-Path $releaseRoot 'portable-dist\Aurora' }
$tools = if ($ToolsDirectory) { [IO.Path]::GetFullPath($ToolsDirectory) } else { Join-Path $releaseRoot 'portable-tools' }
if (-not (Test-Path (Join-Path $dist 'Aurora.exe'))) { throw 'PyInstaller ONEDIR build missing; run build_release.ps1 first.' }
if (-not (Test-Path (Join-Path $dist 'runtime'))) { throw 'Bundled runtime missing; run build_release.ps1 first.' }
if (-not (Test-Path (Join-Path $root 'frontend\dist\index.html'))) { throw 'Production frontend missing; run build_release.ps1 first.' }
if (-not (Test-Path (Join-Path $tools 'AuroraReleaseVerifier.exe'))) { throw 'Standalone release verifier missing; run build_release.ps1 first.' }
if (-not (Test-Path (Join-Path $tools 'Start Aurora.exe'))) { throw 'Start Aurora launcher missing; run build_release.ps1 first.' }
New-Item -ItemType Directory -Path $staging | Out-Null
Copy-Item (Join-Path $dist 'Aurora.exe') $staging
Copy-Item (Join-Path $dist 'runtime') $staging -Recurse
Copy-Item (Join-Path $tools 'Start Aurora.exe') $staging
New-Item -ItemType Directory -Path (Join-Path $staging 'frontend\dist') | Out-Null
Copy-Item (Join-Path $root 'frontend\dist\*') (Join-Path $staging 'frontend\dist') -Recurse
New-Item -ItemType Directory -Path (Join-Path $staging 'resources'),(Join-Path $staging 'scripts') | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'resources\*') (Join-Path $staging 'resources')
Copy-Item (Join-Path $PSScriptRoot 'scripts\*') (Join-Path $staging 'scripts')
Copy-Item (Join-Path $tools 'AuroraReleaseVerifier.exe') (Join-Path $staging 'scripts')
Set-Content -LiteralPath (Join-Path $staging 'VERSION') -Value $Version -NoNewline
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'CHANGELOG.md') -Destination (Join-Path $staging 'CHANGELOG.md')
$readme = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'README.txt') -Raw
if ($UnsignedCandidate) {
  $readme = "UNSIGNED RELEASE CANDIDATE - NOT AN OFFICIAL OR TRUSTED RELEASE. Do not use for production or official updates.`r`n`r`n$readme"
}
[IO.File]::WriteAllText((Join-Path $staging 'README.txt'),$readme,[System.Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $staging 'LICENSE.txt'),(Get-Content (Join-Path $PSScriptRoot 'resources\LICENSE.txt') -Raw),[System.Text.UTF8Encoding]::new($false))
if (-not $UnsignedCandidate) {
  Copy-Item -LiteralPath $PublicKey -Destination (Join-Path $staging 'resources\release_public_key.pem')
}

$env:AURORA_RELEASE_ID = if ($UnsignedCandidate) { "v$Version-$($commit.Trim())-UNSIGNED-RC" } else { "v$Version-$($commit.Trim())" }
$env:AURORA_BUILD_TIMESTAMP_UTC = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
$env:AURORA_RELEASE_NOTES = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'CHANGELOG.md') -Raw)
$env:AURORA_SIGNING_STAGE = $staging
$env:AURORA_RELEASE_VERSION = $Version
if ($UnsignedCandidate) {
  & $python -c "import os,sys;sys.dont_write_bytecode=True;sys.path.insert(0,r'$PSScriptRoot');from release_security import create_unsigned_candidate_manifest;create_unsigned_candidate_manifest(os.environ['AURORA_SIGNING_STAGE'],os.environ['AURORA_RELEASE_VERSION'])"
  if ($LASTEXITCODE) { throw 'Unsigned candidate manifest generation failed.' }
} else {
  & $python -c "import os,sys;sys.dont_write_bytecode=True;sys.path.insert(0,r'$PSScriptRoot');from release_security import sign_staged_package;sign_staged_package(os.environ['AURORA_SIGNING_STAGE'],os.environ['AURORA_RELEASE_PRIVATE_KEY'],os.environ['AURORA_RELEASE_PUBLIC_KEY'],os.environ['AURORA_RELEASE_VERSION'],os.environ['AURORA_RELEASE_KEY_FINGERPRINT'])"
  if ($LASTEXITCODE) { throw 'Manifest signing failed.' }
}
$env:AURORA_CANDIDATE_ZIP = $zipTemp
& $python -c "import os,sys;sys.dont_write_bytecode=True;sys.path.insert(0,r'$PSScriptRoot');from release_security import create_reproducible_zip;create_reproducible_zip(os.environ['AURORA_SIGNING_STAGE'],os.environ['AURORA_CANDIDATE_ZIP'])"
if ($LASTEXITCODE) { throw 'Reproducible ZIP creation failed.' }
if ($UnsignedCandidate) {
  & $python -c "import os,sys;sys.dont_write_bytecode=True;sys.path.insert(0,r'$PSScriptRoot');from release_security import verify_unsigned_candidate;verify_unsigned_candidate(os.environ['AURORA_CANDIDATE_ZIP'])"
  if ($LASTEXITCODE) { throw 'Unsigned candidate integrity validation failed.' }
} else {
  $env:AURORA_CANDIDATE_PUBLIC_KEY = $PublicKey
  & $python -c "import os,sys,zipfile;sys.dont_write_bytecode=True;sys.path.insert(0,r'$PSScriptRoot');from release_security import verify_zip;verify_zip(os.environ['AURORA_CANDIDATE_ZIP'],os.environ['AURORA_CANDIDATE_PUBLIC_KEY'],os.environ['AURORA_RELEASE_KEY_FINGERPRINT']);z=zipfile.ZipFile(os.environ['AURORA_CANDIDATE_ZIP']);bad=z.testzip();z.close();raise SystemExit(1 if bad else 0)"
  if ($LASTEXITCODE) { throw 'Signed candidate ZIP integrity/signature validation failed.' }
}
Move-Item -LiteralPath $zipTemp -Destination $zip
Get-FileHash -Algorithm SHA256 -LiteralPath $zip | ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $zip -Leaf)" } | Set-Content -LiteralPath "$zip.sha256" -Encoding ascii
if ($UnsignedCandidate) { Write-Host "Created unsigned RC $zip. It is not trusted and must not be installed as an official release." }
else { Write-Host "Created $zip. Verify independently with verify_release.ps1 before distribution." }
