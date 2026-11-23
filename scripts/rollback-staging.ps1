param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^aurora-backend:[A-Za-z0-9._-]+$')]
    [string]$BackendImage
)

$ErrorActionPreference = 'Stop'
$env:AURORA_BACKEND_IMAGE = $BackendImage

docker compose -p aurora-staging -f docker-compose.yml -f docker-compose.staging.yml up -d --no-build --force-recreate aurora-backend
if ($LASTEXITCODE -ne 0) { throw 'Could not start the requested backend image.' }

$health = Invoke-RestMethod -Uri 'http://localhost:18000/health' -TimeoutSec 30
if ($health.database -ne 'ok') { throw "Rollback started, but database health is '$($health.database)'." }
Write-Output "Staging backend restored to $BackendImage (Ollama status: $($health.ollama))."
