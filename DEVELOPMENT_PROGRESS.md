# Aurora – Development Progress
**Last Updated:** 2026-11-21

---

## Phase 2 – Stabilization ✅ Completed

**Date:** 2026-11-23

### What was implemented
- Python 3.12.10 venv created at `backend/.venv`
- All 78 backend packages installed including: fastapi, uvicorn, faiss-cpu, sentence-transformers, faster-whisper, pyttsx3, pywin32, pydub, SQLAlchemy, aiosqlite, httpx, aiofiles
- Switched `openai-whisper` → `faster-whisper` (better Python 3.12 + RTX 3050 support; uses CUDA fp16, falls back to CPU int8)
- **Fixed port mismatch**: frontend WS target corrected from `8001` → `8000`
- **Fixed async blocking**: Ollama HTTP call, TTS synthesis, STT transcription, RAG retrieval all wrapped in `asyncio.to_thread()`
- **Added conversation history**: last 10 conversation turns injected into every LLM prompt
- **Added `.env` / `.env.example`**: all config externalized
- **Added `/api/models`** endpoint: lists all Ollama models
- **Added `/api/models/select`** endpoint: switches active model at runtime
- **Rewrote `config.py`**: pydantic-settings + python-dotenv
- **Rewrote `intent_router.py`**: history injection, graceful Ollama error handling, runtime model switch
- **Rewrote `stt.py`**: faster-whisper with CUDA/CPU fallback
- **Created `run.py`**: clean entry point (replaces misleading `aurora.py` stub)
- **Frontend `node_modules`** installed (277 packages)
- **Updated `.gitignore`**: covers venv, .env, vectorstore, bolt artifacts

### Files modified
- `backend/requirements.txt` — updated deps, openai-whisper → faster-whisper
- `backend/app/config.py` — full rewrite with dotenv
- `backend/app/api.py` — full rewrite, async-safe, session history, model endpoints
- `backend/app/intent/intent_router.py` — full rewrite with history + error handling
- `backend/app/perception/stt.py` — full rewrite for faster-whisper
- `backend/app/main.py` — updated
- `frontend/vite.config.ts` — port fix + proxy config
- `.gitignore` — updated

### Files created
- `backend/run.py` — proper entry point
- `backend/.env` — local config (gitignored)
- `backend/.env.example` — template committed to repo

### Tests executed & results
| Test | Result |
|---|---|
| All backend module imports | ✅ PASS |
| Frontend `npm run build` (1476 modules) | ✅ PASS |
| `GET /health` → `{"status":"ok","ollama":true,"model":"llama3.2:3b"}` | ✅ PASS |
| `GET /api/models` → `{"models":["llama3.2:3b"],"active":"llama3.2:3b"}` | ✅ PASS |

### Git checkpoint
Commit: `1d6fa7a` — "Phase 2: Stabilization complete"

### What remains
Phases 3–11 as per roadmap. Next: Phase 3 — Architecture Refactoring (DB layer, logging, clean modules).

---
## Milestone Tracker

| Phase | Name | Status | Updated |
|---|---|---|---|
| 1 | Audit | ✅ Completed | 2026-11-21 |
| 2 | Stabilization | ✅ Completed | 2026-11-23 |
| 3 | Architecture Refactoring | ⏳ Pending | — |
| 4 | Core AI Assistant | ⏳ Pending | — |
| 5 | Memory and RAG | ⏳ Pending | — |
| 6 | Voice | ⏳ Pending | — |
| 7 | Advanced AI | ⏳ Pending | — |
| 8 | UI and UX Polish | ⏳ Pending | — |
| 9 | Testing | ⏳ Pending | — |
| 10 | Desktop Packaging | ⏳ Pending | — |
| 11 | Release | ⏳ Pending | — |

---

## Phase 2 – Stabilization ✅ Completed

**Date:** 2026-11-23

### What was implemented
- Python 3.12.10 venv created at `backend/.venv`
- All 78 backend packages installed including: fastapi, uvicorn, faiss-cpu, sentence-transformers, faster-whisper, pyttsx3, pywin32, pydub, SQLAlchemy, aiosqlite, httpx, aiofiles
- Switched `openai-whisper` → `faster-whisper` (better Python 3.12 + RTX 3050 support; uses CUDA fp16, falls back to CPU int8)
- **Fixed port mismatch**: frontend WS target corrected from `8001` → `8000`
- **Fixed async blocking**: Ollama HTTP call, TTS synthesis, STT transcription, RAG retrieval all wrapped in `asyncio.to_thread()`
- **Added conversation history**: last 10 conversation turns injected into every LLM prompt
- **Added `.env` / `.env.example`**: all config externalized
- **Added `/api/models`** endpoint: lists all Ollama models
- **Added `/api/models/select`** endpoint: switches active model at runtime
- **Rewrote `config.py`**: pydantic-settings + python-dotenv
- **Rewrote `intent_router.py`**: history injection, graceful Ollama error handling, runtime model switch
- **Rewrote `stt.py`**: faster-whisper with CUDA/CPU fallback
- **Created `run.py`**: clean entry point (replaces misleading `aurora.py` stub)
- **Frontend `node_modules`** installed (277 packages)
- **Updated `.gitignore`**: covers venv, .env, vectorstore, bolt artifacts

### Files modified
- `backend/requirements.txt` — updated deps, openai-whisper → faster-whisper
- `backend/app/config.py` — full rewrite with dotenv
- `backend/app/api.py` — full rewrite, async-safe, session history, model endpoints
- `backend/app/intent/intent_router.py` — full rewrite with history + error handling
- `backend/app/perception/stt.py` — full rewrite for faster-whisper
- `backend/app/main.py` — updated
- `frontend/vite.config.ts` — port fix + proxy config
- `.gitignore` — updated

### Files created
- `backend/run.py` — proper entry point
- `backend/.env` — local config (gitignored)
- `backend/.env.example` — template committed to repo

### Tests executed & results
| Test | Result |
|---|---|
| All backend module imports | ✅ PASS |
| Frontend `npm run build` (1476 modules) | ✅ PASS |
| `GET /health` → `{"status":"ok","ollama":true,"model":"llama3.2:3b"}` | ✅ PASS |
| `GET /api/models` → `{"models":["llama3.2:3b"],"active":"llama3.2:3b"}` | ✅ PASS |

### Git checkpoint
Commit: `1d6fa7a` — "Phase 2: Stabilization complete"

### What remains
Phases 3–11 as per roadmap. Next: Phase 3 — Architecture Refactoring (DB layer, logging, clean modules).

---
## Phase 1 – Audit ✅ Completed

**Date:** 2026-11-21

### What was inspected
- All Python backend files: `api.py`, `config.py`, `main.py`, `aurora.py`, `intent_router.py`, `rag_service.py`, `load_documents.py`, `stt.py`, `tts.py`
- All React frontend files: `App.tsx`, `Header.tsx`, `DashboardView.tsx`, `VoiceView.tsx`, `VoiceMicOrb.tsx`, `AIOrb.tsx`, `useAssistantSocket.ts`
- Configuration: `vite.config.ts`, `package.json`, `requirements.txt`, `config.py`
- Runtime environment: Python version, pip packages, Node.js, GPU, Ollama state

### What was implemented
- `PROJECT_AUDIT.md` — full file-by-file audit with issue classification
- `CURRENT_ARCHITECTURE.md` — as-found system map, data flows, port table, dependency matrix
- `FEATURE_STATUS.md` — every feature classified (Working / Partial / Broken / Not Implemented / Unnecessary)
- `DEVELOPMENT_ROADMAP.md` — 11-phase plan with tasks, architecture decisions, blockers

### Files created
- `C:\Aurora\PROJECT_AUDIT.md`
- `C:\Aurora\CURRENT_ARCHITECTURE.md`
- `C:\Aurora\FEATURE_STATUS.md`
- `C:\Aurora\DEVELOPMENT_ROADMAP.md`
- `C:\Aurora\DEVELOPMENT_PROGRESS.md` (this file)

### Problems discovered

**Critical:**
- Python 3.14.2 installed — none of the Aurora ML packages support 3.14 yet
- Backend dependencies NOT installed (no venv, no packages)
- ffmpeg NOT installed — STT voice pipeline is broken
- Port mismatch: backend on 8000, frontend hardcoded to 8001
- Synchronous `requests.post()` and `pyttsx3.runAndWait()` called inside async WebSocket handlers — blocks event loop
- Ollama not running at audit time

**Major:**
- No text chat UI despite the WebSocket hook being implemented
- No conversation history passed to LLM — stateless per turn
- Hardcoded username "Ayoub" in Dashboard
- No persistent storage (no SQLite, no database)
- 8 of 9 planned screens do not exist

**Minor:**
- Hardcoded date in Header
- `aurora.py` is a useless stub
- `.bolt/` IDE artifacts in frontend

### Tests executed
None — environment not set up.

### What remains
All phases 2–11.

### Blockers requiring user input
1. **Python 3.12** — does the user have py 3.12 available, or should we install it?
2. **ffmpeg** — confirm installation preference
3. **Ollama** — which models are currently installed?
4. **Desktop packaging** — PyInstaller, Tauri, or Electron?

---

## Phase 2 – Stabilization ✅ Completed

**Date:** 2026-11-23

### What was implemented
- Python 3.12.10 venv created at `backend/.venv`
- All 78 backend packages installed including: fastapi, uvicorn, faiss-cpu, sentence-transformers, faster-whisper, pyttsx3, pywin32, pydub, SQLAlchemy, aiosqlite, httpx, aiofiles
- Switched `openai-whisper` → `faster-whisper` (better Python 3.12 + RTX 3050 support; uses CUDA fp16, falls back to CPU int8)
- **Fixed port mismatch**: frontend WS target corrected from `8001` → `8000`
- **Fixed async blocking**: Ollama HTTP call, TTS synthesis, STT transcription, RAG retrieval all wrapped in `asyncio.to_thread()`
- **Added conversation history**: last 10 conversation turns injected into every LLM prompt
- **Added `.env` / `.env.example`**: all config externalized
- **Added `/api/models`** endpoint: lists all Ollama models
- **Added `/api/models/select`** endpoint: switches active model at runtime
- **Rewrote `config.py`**: pydantic-settings + python-dotenv
- **Rewrote `intent_router.py`**: history injection, graceful Ollama error handling, runtime model switch
- **Rewrote `stt.py`**: faster-whisper with CUDA/CPU fallback
- **Created `run.py`**: clean entry point (replaces misleading `aurora.py` stub)
- **Frontend `node_modules`** installed (277 packages)
- **Updated `.gitignore`**: covers venv, .env, vectorstore, bolt artifacts

### Files modified
- `backend/requirements.txt` — updated deps, openai-whisper → faster-whisper
- `backend/app/config.py` — full rewrite with dotenv
- `backend/app/api.py` — full rewrite, async-safe, session history, model endpoints
- `backend/app/intent/intent_router.py` — full rewrite with history + error handling
- `backend/app/perception/stt.py` — full rewrite for faster-whisper
- `backend/app/main.py` — updated
- `frontend/vite.config.ts` — port fix + proxy config
- `.gitignore` — updated

### Files created
- `backend/run.py` — proper entry point
- `backend/.env` — local config (gitignored)
- `backend/.env.example` — template committed to repo

### Tests executed & results
| Test | Result |
|---|---|
| All backend module imports | ✅ PASS |
| Frontend `npm run build` (1476 modules) | ✅ PASS |
| `GET /health` → `{"status":"ok","ollama":true,"model":"llama3.2:3b"}` | ✅ PASS |
| `GET /api/models` → `{"models":["llama3.2:3b"],"active":"llama3.2:3b"}` | ✅ PASS |

### Git checkpoint
Commit: `1d6fa7a` — "Phase 2: Stabilization complete"

### What remains
Phases 3–11 as per roadmap. Next: Phase 3 — Architecture Refactoring (DB layer, logging, clean modules).

---
## Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-11-21 | Use Python 3.12 venv for backend | ML packages lack Python 3.14 wheels |
| 2026-11-21 | Keep React frontend | VoiceMicOrb and WS hook are reusable; migration to Electron/Tauri premature |
| 2026-11-21 | Use SQLite for persistence | No external server; single file; built into Python |
| 2026-11-21 | Use asyncio.to_thread() for blocking calls | Avoids event loop blocking without replacing pyttsx3/whisper |
