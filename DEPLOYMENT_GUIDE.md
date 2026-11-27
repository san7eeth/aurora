# Deployment Guide

## Local Docker Compose

Requirements: Docker Desktop with Compose; Ollama on the host for model-backed features. From `C:\Aurora`:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8000/health
```

Frontend: `http://localhost:5173`. Backend health/metrics: `http://localhost:8000/health` and `/metrics`. Compose binds ports to loopback by default. Configure the local `.env` before using optional settings. Ollama remains on the host and is reached through `host.docker.internal`.

Stop services with `docker compose down`. This preserves named volumes. `docker compose down -v` deletes persisted application and monitoring data; use it only when intentionally resetting local state.

## Optional services

```powershell
docker compose --profile devtools up -d sonarqube
docker compose --profile monitoring up -d
```

SonarQube is on port 9000; Prometheus on 9090; Grafana on 3000. Set a private `GRAFANA_ADMIN_PASSWORD` in `.env` before starting Grafana beyond a disposable local session. Jenkins and SonarQube credentials must be configured in their local interfaces and must not be committed.

## Staging

```powershell
$env:AURORA_BACKEND_IMAGE = 'aurora-backend:local'
$env:AURORA_FRONTEND_IMAGE = 'aurora-frontend:local'
docker compose -p aurora-staging -f docker-compose.yml -f docker-compose.staging.yml up --build -d
Invoke-RestMethod http://localhost:18000/health
```

Frontend staging URL: `http://localhost:18080`. The Jenkins pipeline has its own staging approval. This repository configuration has not been exercised against a live external host as of the status recorded in [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md).

Rollback to a retained backend image:

```powershell
./scripts/rollback-staging.ps1 -BackendImage aurora-backend:<known-good-tag>
```

The tag must exist locally. Validate health and user flows after rollback. See [devops/README.md](devops/README.md) for CI, release, and troubleshooting details.

## Windows desktop package

The Phase 10 script builds a PyInstaller executable and, when Inno Setup is installed, a per-user installer. Run it on Windows with the Python 3.12 backend environment, Node.js, and frontend dependencies:

```powershell
./packaging/windows/Build-WindowsPackage.ps1 -Version 0.3.0
```

The runnable package is in `release/Aurora/`; installer output is in `release/installer/`. Start with `Start-Aurora.ps1` or the Start Menu shortcut. Stop cleanly with `Stop-Aurora.ps1`. The app opens at `http://127.0.0.1:8000/`; user data lives under `%LOCALAPPDATA%\Aurora`. Ollama remains host-managed. See [packaging/README.md](packaging/README.md) for prerequisites and verification limits.
# Portable Windows x64 release

The ONEDIR build scripts are in `packaging/portable`. Use Windows x64, Python 3.12, Node.js, and PyInstaller 6.22.3. Run `packaging/portable/build_release.ps1`; after that run `package_portable.ps1 -Version 1.0.0` with `AURORA_RELEASE_PRIVATE_KEY`, `AURORA_RELEASE_PUBLIC_KEY`, and `AURORA_RELEASE_KEY_FINGERPRINT` set to developer-controlled values. Signing keys must be stored outside the checkout. The script fails closed when they are missing. Do not publish a package until it verifies with an independently pinned fingerprint and passes the clean Windows VM gates in `TESTING_GUIDE.md`.

The target filename is `Aurora-v1.0.0-Windows-x64-Portable.zip`. GitHub Actions uses the protected `aurora-release` environment. A repository administrator must create that environment, require an authorized reviewer, add `AURORA_RELEASE_PRIVATE_KEY` and `AURORA_RELEASE_PUBLIC_KEY` as environment secrets, and set `AURORA_RELEASE_KEY_FINGERPRINT` as an environment variable to the SHA-256 fingerprint of the raw Ed25519 public key. Distribute that fingerprint through an independent official channel. No official signing key has been provisioned in this workspace.
