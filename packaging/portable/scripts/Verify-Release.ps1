param([Parameter(Mandatory=$true)][string]$PackagePath,[Parameter(Mandatory=$true)][string]$Fingerprint,[string]$PublicKey=(Join-Path $PSScriptRoot '..\resources\release_public_key.pem'))
$ErrorActionPreference='Stop'
$verifier=Join-Path $PSScriptRoot 'AuroraReleaseVerifier.exe'
if (-not (Test-Path $verifier)) { throw 'AuroraReleaseVerifier.exe is missing from this package.' }
& $verifier --zip (Resolve-Path $PackagePath).Path --public-key (Resolve-Path $PublicKey).Path --fingerprint $Fingerprint
if ($LASTEXITCODE) { throw 'Package verification failed. Do not extract or run it.' }
