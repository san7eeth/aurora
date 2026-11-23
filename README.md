# Aurora

Aurora is a locally hosted AI assistant with a FastAPI backend, React frontend, SQLite persistence, Ollama integration, voice support, and an optional allowlisted agent workflow.

## Local development

Requirements: Docker Desktop with Compose, and Ollama running on the host for model-backed features. Ollama remains host-managed; Compose connects to `host.docker.internal:11434` and does not assume GPU access from the app containers.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

Open `http://localhost:5173`, backend health at `http://localhost:8000/health`, and request metrics at `http://localhost:8000/metrics`. Use `docker compose logs -f aurora-backend` to inspect JSON logs. Stop with `docker compose down`; use `docker compose down -v` only when you intend to delete local data.

The interface includes a first-run personalization wizard, responsive screen navigation, and a service status dashboard. Shortcuts: `Ctrl/⌘+N` starts a chat, `Alt+1–8` opens a screen, and `?` shows shortcut help. Phase 8 builds successfully, but browser interaction checks are pending because the Playwright Chromium binary is unavailable here. Phase 9 adds backend test coverage; its synchronous subset passes while async/API tests need a socket-enabled runner. See [`DEVELOPMENT_PROGRESS.md`](DEVELOPMENT_PROGRESS.md).

Development/DevOps workflows are in [`devops/README.md`](devops/README.md). Operational details are in [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md), security boundaries in [`SECURITY.md`](SECURITY.md), and verification commands in [`TESTING_GUIDE.md`](TESTING_GUIDE.md). Jira is documented for manual workflows; there is no Jira API integration.

Windows packaging uses PyInstaller to bundle FastAPI and the built React frontend; the local UI opens in a browser and keeps user data under `%LOCALAPPDATA%\Aurora`. See [`packaging/README.md`](packaging/README.md). Ollama remains separately installed on the host.

## Project structure

- `backend/` — FastAPI, SQLite services, allowlisted tools, and Python tests.
- `frontend/` — React/Vite app and production Nginx container.
- `e2e-playwright/` — Playwright browser and API smoke checks.
- `qa-java/` — separate Maven/TestNG/Selenium/REST Assured/Cucumber learning module.
- `devops/` — Jenkins image and Prometheus/Grafana configuration.
- `DEVELOPMENT_ROADMAP.md` — phased implementation and status.
- `DEVELOPMENT_PROGRESS.md` — milestone tasks, changed files, checks, issues, and next milestone.
- `ARCHITECTURE.md` — current component and data-flow overview.
- `LEARNING_NOTES.md` and `CHANGELOG.md` — development lessons and user-facing change history.

## Security basics

Never commit `.env`, credentials, tokens, local databases, uploaded documents, voice recordings, or clipboard content. Agent plans are previewed and require approval; tools are allowlisted. Approximate voice matching is not an authentication or authorization control.
