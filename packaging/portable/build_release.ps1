param([switch]$SkipFrontendBuild, [switch]$SkipClean, [string]$OutputRoot)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$releaseRoot = if ($OutputRoot) { [IO.Path]::GetFullPath($OutputRoot) } else { Join-Path $root 'release' }
if ($OutputRoot -and (Test-Path -LiteralPath $releaseRoot)) { throw "Refusing to overwrite existing output root: $releaseRoot" }
New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null
if ($env:OS -ne 'Windows_NT') { throw 'Portable release builds require Windows x64.' }
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Create backend\.venv with Python 3.12 and install backend requirements first.' }
$architecture = & $python -c 'import platform; print(platform.machine().lower())'
$pythonVersion = & $python -c 'import sys; print(str(sys.version_info.major) + chr(46) + str(sys.version_info.minor))'
if ($architecture -notin @('amd64','x86_64')) { throw 'Use a 64-bit Python build on Windows x64.' }
if ($pythonVersion -ne '3.12') { throw 'Use Python 3.12.' }
& $python -m pip install -r (Join-Path $root 'backend\requirements.txt') -r (Join-Path $PSScriptRoot 'requirements-packaging.txt')
if ($LASTEXITCODE) { throw 'Python dependency installation failed.' }
if (-not $SkipFrontendBuild) {
  Push-Location (Join-Path $root 'frontend')
  try { npm ci; if ($LASTEXITCODE) { throw 'npm ci failed' }; npm run lint; if ($LASTEXITCODE) { throw 'Frontend lint failed' }; npm run build; if ($LASTEXITCODE) { throw 'Frontend build failed' } }
  finally { Pop-Location }
}
$cleanArgs = @()
if (-not $SkipClean) { $cleanArgs = @('--clean') }
& $python -m PyInstaller --noconfirm @cleanArgs --distpath (Join-Path $releaseRoot 'portable-dist') --workpath (Join-Path $releaseRoot 'portable-build') (Join-Path $PSScriptRoot 'aurora.spec')
if ($LASTEXITCODE) { throw 'PyInstaller ONEDIR build failed' }
$portableDist = Join-Path $releaseRoot 'portable-dist\Aurora'
New-Item -ItemType Directory -Force (Join-Path $portableDist 'frontend\dist') | Out-Null
Copy-Item (Join-Path $root 'frontend\dist\*') (Join-Path $portableDist 'frontend\dist') -Recurse -Force
& $python -m PyInstaller --noconfirm --clean --onefile --console --name AuroraReleaseVerifier --distpath (Join-Path $releaseRoot 'portable-tools') --workpath (Join-Path $releaseRoot 'verifier-build') --specpath (Join-Path $releaseRoot 'verifier-spec') --paths $PSScriptRoot --hidden-import cryptography.hazmat.bindings._rust (Join-Path $PSScriptRoot 'verify_release.py')
if ($LASTEXITCODE) { throw 'Verifier build failed' }
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name 'Start Aurora' --distpath (Join-Path $releaseRoot 'portable-tools') --workpath (Join-Path $releaseRoot 'launcher-build') --specpath (Join-Path $releaseRoot 'launcher-spec') (Join-Path $PSScriptRoot 'start_aurora.py')
if ($LASTEXITCODE) { throw 'Start Aurora launcher build failed' }
Write-Host "Build complete in $releaseRoot. Run package_portable.ps1 with the selected release mode."
