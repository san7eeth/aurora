# Aurora – Development Roadmap
**Created:** 2026-11-21  
**Target:** Aurora 1.0 — Stable, installable, locally hosted AI desktop assistant

---

## Architecture Decision: Python 3.12 Virtual Environment

**Decision:** Create a Python 3.12 virtual environment for the backend.  
**Reason:** Python 3.14.2 is too new for `faiss-cpu`, `openai-whisper`, and `torch` wheels. 3.12 is the most broadly supported version for all ML/AI packages in this stack.  
**Action required from user:** Install Python 3.12 alongside existing 3.14, or use `py -3.12` launcher.

---

## Architecture Decision: Keep React Frontend, Extend Significantly

**Decision:** Keep the existing React + Vite + Tailwind stack. Add all missing screens.  
**Reason:** `VoiceMicOrb.tsx` and the WebSocket hook are genuinely good. Rewriting in Electron or Tauri would delay the project by weeks and add complexity.  
**Desktop packaging:** Use **Tauri** (Rust-based) or **Electron** in Phase 10 to wrap the frontend into a `.exe` installer. Decision to be confirmed before Phase 10.

---

## Architecture Decision: SQLite for Persistence

**Decision:** Use SQLite (via Python's built-in `sqlite3` or `SQLAlchemy`) for all persistence.  
**Reason:** No external database server; single file; easy backup; works on all platforms.

---

## Architecture Decision: Fix Async Blocking — Use `asyncio.to_thread()`

**Decision:** Wrap all synchronous calls (Ollama HTTP, pyttsx3, Whisper) in `asyncio.to_thread()` to offload to a thread pool without blocking the event loop.  
**Reason:** FastAPI / uvicorn run on asyncio; blocking the event loop freezes all WebSocket connections.

---

## Phase Plan

### Phase 1 – Audit ✅ COMPLETED
**Output:** `PROJECT_AUDIT.md`, `CURRENT_ARCHITECTURE.md`, `FEATURE_STATUS.md`, `DEVELOPMENT_ROADMAP.md`

---

### Phase 2 – Stabilization
**Goal:** Make the backend startable and the frontend connectable.

Tasks:
- [ ] Create Python 3.12 virtual environment (`backend/.venv`)
- [ ] Install all backend dependencies
- [ ] Fix port mismatch (backend: 8000, frontend target: 8001 → align to 8000)
- [ ] Wrap synchronous Ollama call in `asyncio.to_thread()`
- [ ] Wrap synchronous TTS call in `asyncio.to_thread()`
- [ ] Add `.env` support via `python-dotenv`
- [ ] Create `.env.example` file
- [ ] Install frontend `node_modules`
- [ ] Fix frontend default to dark mode
- [ ] Fix `Header.tsx` to show real clock
- [ ] Fix connection status dot in Header
- [ ] Install ffmpeg or document clearly as prerequisite
- [ ] Test backend startup with `uvicorn`
- [ ] Test frontend startup with `npm run dev`
- [ ] Test WebSocket connection end-to-end

---

### Phase 3 – Architecture Refactoring
**Goal:** Clean module boundaries, database layer, logging.

Tasks:
- [ ] Remove `aurora.py` stub; create proper `run.py` entry point
- [ ] Remove `.bolt/` directory from frontend
- [ ] Remove `backend/package-lock.json`
- [ ] Create `backend/app/database/` module with SQLite schema
- [ ] Create `backend/app/core/` with logging, config, exceptions
- [ ] Create `backend/app/services/` with clean service interfaces
- [ ] Add structured JSON logging
- [ ] Create `.env` and `.env.example`
- [ ] Add startup health checks (Ollama ping, DB init)

---

### Phase 4 – Core AI Assistant
**Goal:** Working text chat with conversation history and model management.

Tasks:
- [ ] Add `/api/models` endpoint (list available Ollama models)
- [ ] Add `/api/models/active` endpoint (get/set current model)
- [ ] Add streaming `/ws` endpoint using Ollama `stream: True`
- [ ] Implement conversation history (last N turns passed to LLM)
- [ ] Persist conversation messages to SQLite
- [ ] Create conversation REST API (list, get, create, delete)
- [ ] Build **Chat screen** in React (message list, text input, send button)
- [ ] Build **Conversation history screen** (list past conversations)
- [ ] Build **Model management screen** (list models, select active)
- [ ] Update Header with live connection status and active model

---

### Phase 5 – Memory and RAG
**Goal:** Persistent long-term memory and document intelligence with management UI.

Tasks:
- [ ] Design memory schema (SQLite table: memories + embeddings)
- [ ] Implement memory extraction (after each conversation turn, extract facts)
- [ ] Implement semantic memory retrieval (merge with RAG results)
- [ ] Add document file upload endpoint (`POST /api/documents/upload`)
- [ ] Add document list endpoint (`GET /api/documents`)
- [ ] Add document delete endpoint (`DELETE /api/documents/{id}`)
- [ ] Add chunk-level metadata (source file, page, chunk index)
- [ ] Build **Knowledge base screen** (upload, list, delete documents)
- [ ] Build **Memory management screen** (view, edit, delete memories)
- [ ] Add document reference display in chat responses

---

### Phase 6 – Voice
**Goal:** Reliable, interruptible voice conversation.

Tasks:
- [ ] Integrate `webrtcvad` or `silero-vad` for proper voice activity detection
- [ ] Replace 100KB byte-threshold with VAD-driven segmentation
- [ ] Add configurable speech rate to settings API
- [ ] Add microphone selection to frontend settings
- [ ] Add interrupt/stop speech button to voice UI
- [ ] Test full voice → STT → LLM → TTS → audio playback loop
- [ ] Handle ffmpeg-not-found gracefully with clear error message
- [ ] Build **Voice settings panel** in settings screen

---

### Phase 7 – Advanced AI
**Goal:** Voice authentication, agentic tool execution, desktop automation.

Tasks:
- [ ] Voice enrollment: record and store voice embeddings (speaker verification)
- [ ] Voice verification: compare incoming audio to stored profile
- [ ] Tool calling framework: define tool schemas, dispatch, result injection
- [ ] Implement safe tools: system info, file list, app launch, clipboard read
- [ ] Implement task planning: multi-step tool sequences
- [ ] Add confirmation UI for sensitive actions
- [ ] Add execution history to database
- [ ] Build **Agent / task management screen**

---

### Phase 8 – UI and UX Polish
**Goal:** Premium, dark-themed, polished desktop experience.

Tasks:
- [ ] Apply consistent dark theme (black/charcoal backgrounds, cyan/blue accents)
- [ ] Add side navigation bar with all screens
- [ ] Add smooth page transitions (Framer Motion)
- [ ] Add system status panel (Ollama status, model loaded, memory usage)
- [ ] Add first-run setup wizard (username, model selection, voice enrollment)
- [ ] Polish all existing screens
- [ ] Add keyboard shortcuts
- [ ] Add error boundary components

---

### Phase 9 – Testing
**Goal:** Test coverage for all critical paths.

Tests to create:
- [ ] `test_startup.py` — backend starts, health endpoint returns 200
- [ ] `test_ollama.py` — Ollama connectivity, model listing
- [ ] `test_websocket.py` — WS connect, message, disconnect
- [ ] `test_streaming.py` — streaming tokens arrive incrementally
- [ ] `test_rag.py` — document ingest, retrieve, answer
- [ ] `test_memory.py` — memory store, retrieve, delete
- [ ] `test_database.py` — SQLite init, CRUD operations
- [ ] `test_tts.py` — synthesis produces non-empty bytes
- [ ] `test_stt.py` — transcription returns text from WAV fixture
- [ ] `test_voice_auth.py` — enroll, verify, reject
- [ ] `test_tools.py` — tool dispatch, safe execution
- [ ] `test_error_handling.py` — Ollama down, corrupt file, bad session

---

### Phase 10 – Desktop Packaging
**Goal:** Installable Windows `.exe`.

**Decision to be confirmed before this phase:**
- **Option A: Tauri** — Rust + WebView2; small installer (~10MB); requires Rust toolchain
- **Option B: Electron** — Node.js; larger installer (~150MB); simpler setup
- **Option C: PyInstaller + Vite build** — bundle FastAPI as `.exe` + serve built frontend; no Electron

Recommended: **Option C** (simplest; no new runtimes; ships as `aurora.exe` + `frontend/` build).

Tasks:
- [ ] Build frontend (`npm run build`)
- [ ] Serve frontend static files from FastAPI (mount `/` → `dist/`)
- [ ] Package backend with PyInstaller into single `.exe`
- [ ] Create NSIS or Inno Setup installer script
- [ ] Add application icon
- [ ] Create startup/shutdown scripts
- [ ] Test installation on clean Windows system

---

### Phase 11 – Release
**Goal:** Aurora 1.0 release package.

Tasks:
- [ ] Write `README.md`
- [ ] Write `INSTALLATION.md`
- [ ] Write `USER_GUIDE.md`
- [ ] Write `CHANGELOG.md`
- [ ] Final end-to-end test run
- [ ] Create GitHub release with installer

---

## Timeline Estimate

| Phase | Effort | Complexity |
|---|---|---|
| 1 – Audit | ✅ Done | — |
| 2 – Stabilization | ~1 session | Low |
| 3 – Refactoring | ~1 session | Medium |
| 4 – Core AI | ~2 sessions | High |
| 5 – Memory + RAG | ~2 sessions | High |
| 6 – Voice | ~1 session | Medium |
| 7 – Advanced AI | ~2 sessions | Very High |
| 8 – UI Polish | ~1 session | Medium |
| 9 – Testing | ~1 session | Medium |
| 10 – Packaging | ~1 session | Medium |
| 11 – Release | ~0.5 session | Low |

---

## Blockers Requiring User Input

| # | Blocker | Decision Needed |
|---|---|---|
| B1 | Python 3.14.2 installed globally — most ML packages lack 3.14 wheels | Install Python 3.12 or use `py -3.12`? |
| B2 | ffmpeg not installed | Install ffmpeg for voice features? |
| B3 | Ollama not running | Start Ollama and confirm which models are installed |
| B4 | Desktop packaging method (Phase 10) | PyInstaller + static serve, Tauri, or Electron? |

**These blockers must be resolved before Phase 2 can complete. All other phases can proceed once Python 3.12 and Ollama are available.**
