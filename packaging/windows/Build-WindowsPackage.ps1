param(
    [string]$Version = '0.3.0',
    [switch]$SkipInstallerCompile,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$backendRoot = Join-Path $repoRoot 'backend'
$python = Join-Path $backendRoot '.venv\Scripts\python.exe'
$packagingRequirements = Join-Path $backendRoot 'requirements-packaging.txt'
$frontendRoot = Join-Path $repoRoot 'frontend'
$releaseRoot = Join-Path $repoRoot 'release'
$distRoot = Join-Path $releaseRoot 'pyinstaller'
$appRoot = Join-Path $releaseRoot 'Aurora'

if (-not $IsWindows -and $env:OS -ne 'Windows_NT') {
    throw 'Build the Windows package on Windows with a 64-bit Python 3.12 environment.'
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend venv was not found. Create it with Python 3.12, then install $packagingRequirements."
}

& $python -m pip show pyinstaller *> $null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is missing. Install it with: $python -m pip install -r $packagingRequirements"
}

if (-not $SkipFrontendBuild) {
    Push-Location $frontendRoot
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
        $env:VITE_WS_BASE = 'ws://127.0.0.1:8000'
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally {
        Remove-Item Env:VITE_WS_BASE -ErrorAction SilentlyContinue
        Pop-Location
    }
} elseif (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'dist\index.html'))) {
    throw 'The production frontend bundle is missing. Run npm run build in frontend/ or omit -SkipFrontendBuild.'
}

New-Item -ItemType Directory -Force -Path $distRoot, $appRoot | Out-Null
Push-Location $repoRoot
try {
    & $python -m PyInstaller --clean --noconfirm --distpath $distRoot --workpath (Join-Path $releaseRoot 'build') (Join-Path $PSScriptRoot 'aurora.spec')
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
} finally { Pop-Location }

$exePath = Join-Path $distRoot 'Aurora.exe'
if (-not (Test-Path -LiteralPath $exePath)) { throw "PyInstaller output was not found: $exePath" }
Copy-Item -LiteralPath $exePath -Destination (Join-Path $appRoot 'Aurora.exe') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Start-Aurora.ps1') -Destination $appRoot -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Stop-Aurora.ps1') -Destination $appRoot -Force
Copy-Item -LiteralPath (Join-Path $repoRoot 'packaging\assets\aurora.ico') -Destination $appRoot -Force

if (-not $SkipInstallerCompile) {
    $isccPath = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source
    if (-not $isccPath) {
        foreach ($candidate in @(
            'C:\Program Files (x86)\Inno Setup 7\ISCC.exe',
            'C:\Program Files\Inno Setup 7\ISCC.exe',
            'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
            'C:\Program Files\Inno Setup 6\ISCC.exe'
        )) {
            if (Test-Path -LiteralPath $candidate) { $isccPath = $candidate; break }
        }
    }
    if (-not $isccPath) {
        throw 'Inno Setup compiler is missing. Install Inno Setup 7, then rerun this script; the runnable Aurora folder is already in release/Aurora.'
    }
    $installerOutput = Join-Path $releaseRoot 'installer'
    New-Item -ItemType Directory -Force -Path $installerOutput | Out-Null
    & $isccPath "/DAppVersion=$Version" "/O$installerOutput" (Join-Path $PSScriptRoot 'Aurora.iss')
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup installer compilation failed.' }
}

Write-Output "Runnable package: $appRoot"
if (-not $SkipInstallerCompile) { Write-Output ("Installer output: " + (Join-Path $releaseRoot 'installer')) }
