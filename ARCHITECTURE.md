# Aurora Architecture

**Status date:** 2026-11-23. This describes the current repository design; runtime behavior still requires the checks listed in [TESTING_GUIDE.md](TESTING_GUIDE.md).

## Components

- **Frontend:** React + TypeScript + Vite. In production, Nginx serves the static bundle and proxies `/api`, `/health`, and `/ws` to the backend.
- **UI shell:** Responsive eight-screen navigation, route transitions, first-run settings wizard, service-status dashboard, theme toggle, keyboard shortcuts, and top-level error boundary. Interaction tests are still pending.
- **Backend:** FastAPI with REST and WebSocket interfaces, async SQLAlchemy services, Ollama integration, voice processing, document retrieval, and allowlisted agent tools.
- Heavy RAG/model dependencies are loaded when RAG is first used, not during a basic API import.
- **Persistence:** SQLite in a local file (`backend/data/aurora.db` in native development; `/app/data/aurora.db` in Compose) with a named volume in the container setup.
- **Model runtime:** Ollama is external and host-managed. Docker reaches it at `host.docker.internal:11434`; the application containers do not assume GPU access.
- **Quality/operations:** Pytest, Playwright, and a separate Java QA learning module; GitHub Actions/Jenkins; optional SonarQube, Prometheus, and Grafana.

## Request paths

```text
Browser → Vite (development) or Nginx (container) → FastAPI
                                                  ├─ REST: settings, models, chat, memory, documents, agent, voice profile
                                                  ├─ WebSocket: streaming assistant and audio conversation
                                                  ├─ SQLite: conversations, settings, memories, documents, plans
                                                  └─ Ollama: model discovery and generation (host-managed)
```

The RAG and memory services use local embeddings/indexing; uploaded documents and generated artifacts remain local. Agent tools are allowlisted and plans require explicit user confirmation. Voice matching is approximate and is not an authorization mechanism.

## Portable Windows runtime

The ONEDIR build keeps immutable runtime/frontend files beside `Aurora.exe`; per-user mutable data is rooted at `%LOCALAPPDATA%\Aurora` under `config/`, `database/`, `conversations/`, `faiss_index/`, `documents/`, `logs/`, and `backups/`. The launcher binds only to `127.0.0.1`. It migrates the prior flat database, `docs/`, and `vectorstore/` by copying files without overwriting files in the new layout. Current source uses FastAPI WebSockets and direct FAISS; it does not use Socket.IO or LangChain, so those unused frameworks are not bundled.

## Deployment topology

Compose has a backend and frontend as the core application. Optional profiles add isolated QA containers (`qa`), SonarQube (`devtools`), and Prometheus/Grafana (`monitoring`). SQLite is embedded, so there is no database service. Staging Compose overrides ports to 18000/18080. Local host port mappings bind to loopback by default.

The Windows package bundles FastAPI, the compiled frontend, and Python dependencies into a PyInstaller executable. It serves the same-origin frontend and API on loopback port 8000. Packaged databases, uploads, embeddings, model cache, and logs live in the current user's `%LOCALAPPDATA%\Aurora`; Ollama remains host-installed.

See [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) for the original as-found audit and [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for commands.
