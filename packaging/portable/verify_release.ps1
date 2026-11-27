param([Parameter(Mandatory=$true)][string]$Zip,[string]$PublicKey=(Join-Path $PSScriptRoot 'resources\release_public_key.pem'),[string]$Fingerprint=$env:AURORA_RELEASE_KEY_FINGERPRINT)
$ErrorActionPreference='Stop'
if (-not $Fingerprint) { throw 'Provide the trusted key fingerprint obtained independently from the official release channel.' }
$verifier=Join-Path $PSScriptRoot '..\..\release\portable-tools\AuroraReleaseVerifier.exe'
if (-not (Test-Path $verifier)) { $verifier=Join-Path $PSScriptRoot 'AuroraReleaseVerifier.exe' }
if (-not (Test-Path $verifier)) { throw 'Bundled AuroraReleaseVerifier.exe is required; Python is not used for user verification.' }
& $verifier --zip (Resolve-Path $Zip).Path --public-key (Resolve-Path $PublicKey).Path --fingerprint $Fingerprint
if ($LASTEXITCODE) { throw 'Release verification failed.' }
