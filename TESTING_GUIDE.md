# Testing and Verification Guide

Run commands from `C:\Aurora` unless a command names another directory. Automated suites are configured, but each result must be recorded when actually run; configuration alone is not a passing test.

## Fast local checks

```powershell
python -m compileall -q backend/app backend/tests
Push-Location frontend
npm run lint
npx tsc --noEmit -p tsconfig.app.json
npm run build
Pop-Location
docker compose config --quiet
```

## Backend tests

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests/unit -v --junitxml=test-results/backend-unit.xml
python -m pytest backend/tests/integration -v -m integration --junitxml=test-results/backend-integration.xml
```

The test fixtures mock Ollama and retrieval. These tests do not prove live model, microphone, audio-device, or deployment behavior.

The suite now includes targeted startup, Ollama HTTP, WebSocket, streaming, RAG, memory/database CRUD, TTS/STT, voice profile, tool allowlist, and malformed-input coverage. API fixtures use temporary SQLite databases to avoid touching the local app database. Some tests are async and require an environment where Python can create its event-loop socket pair; run the full commands in CI if the local sandbox blocks that operation. A skipped or blocked test is not a pass.

## Browser/API smoke tests

Start the app with `docker compose up --build -d`, then run:

```powershell
Push-Location e2e-playwright
npm ci
npx playwright install chromium
npm test
Pop-Location
```

Use the `AURORA_URL`, `BACKEND_URL`, and `PLAYWRIGHT_OUTPUT_DIR` environment variables to target another environment and save reports.

## Java QA module

With a running backend and browser (or configured Selenium Grid):

```powershell
mvn -f qa-java/pom.xml -Dtest=AuroraAPITest test
mvn -f qa-java/pom.xml -Dtest=AuroraBDDTest test
$env:AURORA_URL = 'http://localhost:5173'
$env:BACKEND_URL = 'http://localhost:8000'
mvn -f qa-java/pom.xml -Dtest=AuroraUITest test
```

## Desktop package smoke check

After the Windows build succeeds, install the generated setup file in a clean Windows account or VM. Confirm the shortcut opens `http://127.0.0.1:8000/`, `/health` reports database status, conversations persist across restart, a document can be uploaded and removed, logs appear under `%LOCALAPPDATA%\Aurora\logs`, and `Stop-Aurora.ps1` shuts the server down cleanly. Confirm uninstall stops Aurora while preserving the user's database and documents. A successful PyInstaller build or script parse alone does not verify installation behavior.

## Record results

For each milestone, record the exact commands executed, pass/fail/blocked result, environment constraints, known issues, and next milestone in [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md). Never mark a feature verified based only on a configured workflow or a successful compile.
