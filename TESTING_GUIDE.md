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
python -m pytest -c backend\pytest.ini backend\tests -q
python -m pytest backend/tests/unit -v --junitxml=test-results/backend-unit.xml
python -m pytest backend/tests/integration -v -m integration --junitxml=test-results/backend-integration.xml
```

The test fixtures mock Ollama and retrieval. These tests do not prove live model, microphone, audio-device, or deployment behavior.

The suite includes startup, Ollama HTTP, WebSocket, streaming, RAG, memory/database CRUD, TTS/STT, voice profile, tool allowlist, malformed-input, portable-launcher, and release-integrity coverage. API fixtures use temporary SQLite databases to avoid touching the local app database. `pytest-asyncio==0.24.0` is pinned so `asyncio_mode` and `asyncio_default_fixture_loop_scope` are recognized. A local full-suite run on 2026-11-27 passed 119 tests with two upstream deprecation warnings (Starlette's `multipart` import and AnyIO's `BlockingPortal` alias); see `RELEASE_VALIDATION_REPORT.md` for the exact command and output. Do not treat this suite as proof of clean-machine or live-device behavior.

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
# Portable release checks

The clean Windows x64 matrix must exercise FAISS index operations and SentenceTransformer embeddings in the same frozen process. A current Windows source smoke exposed conflicting `libomp140` and `libiomp5md` OpenMP runtimes when FAISS and Torch are initialized together. Keep the portable RAG release gate open until that is resolved through a supported dependency/runtime combination.

The focused unit checks are `backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_portable_runtime_paths.py backend/tests/unit/test_release_security.py -q`. Build checks require Windows x64, Python 3.12, PyInstaller 6.22.3 and frontend assets. On a clean Windows 10/11 x64 VM without Python/Node, verify signature and hashes before extraction, start `Aurora.exe`, test FastAPI and FAISS, verify Ollama/model missing setup, operate offline after model download, update while preserving user data, reject altered/unsigned artifacts, and execute backup/restore/rollback. Record VM image, OS build, test date, commands, and results before calling a release complete. This workspace has not completed that VM matrix.
