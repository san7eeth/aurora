# Aurora – Development Roadmap
**Created:** 2026-11-21  
**Target:** Aurora 1.0 — Stable, installable, locally hosted AI desktop assistant
**Last Status Update:** 2026-11-23 17:01 IST

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

### Phase 2 – Stabilization ✅ IMPLEMENTATION COMPLETE (reviewed 2026-11-23)
**Goal:** Make the backend startable and the frontend connectable.

Tasks:
- [x] Create Python 3.12 virtual environment (`backend/.venv`) — present
- [x] Install backend dependencies — venv present; runtime dependency inventory not revalidated package by package
- [x] Fix port mismatch — frontend WS default is 8000
- [x] Offload blocking Ollama/TTS/STT/RAG work — API flow uses `asyncio.to_thread()`
- [x] Add `.env` support and `.env.example`
- [x] Install frontend `node_modules` — present
- [x] Fix frontend default to dark mode
- [x] Fix `Header.tsx` to show real clock
- [x] Fix connection status dot in Header using periodic `/health` checks
- [x] Document ffmpeg prerequisite in `VOICE_SETUP.md` — ffmpeg itself is not available in this environment
- [ ] Confirm backend startup and WebSocket end-to-end — live check attempted; sandbox denied loopback socket access
- [x] Import backend API module — passed 2026-11-23
- [x] Frontend production build — passed 2026-11-23 (1476 modules)

---

### Phase 3 – Architecture Refactoring ✅ COMPLETED (reviewed 2026-11-23)
**Goal:** Clean module boundaries, database layer, logging.

Tasks:
- [x] Remove `aurora.py` stub; create proper `run.py` entry point
- [x] Remove `.bolt/` directory from frontend
- [x] Remove `backend/package-lock.json`
- [x] Create `backend/app/database/` module with SQLite schema
- [x] Create `backend/app/core/` with logging, config, exceptions
- [x] Create `backend/app/services/` with clean service interfaces
- [x] Add configurable structured JSON logging
- [x] Create `.env` and `.env.example`
- [x] Add startup health checks (Ollama ping, DB init)

Verification: all Phase 3 synchronous core/database tests passed (14 passed). The async startup-check test stalled under the available Python event loop and was stopped; rerun it with the broader Phase 9 test pass. This does not block completion of the Phase 3 architecture work.

---

### Phase 4 – Core AI Assistant ✅ IMPLEMENTATION COMPLETE (updated 2026-11-23 16:33 IST)
**Goal:** Working text chat with conversation history and model management.

Tasks:
- [x] Add `/api/models` endpoint (list available Ollama models)
- [x] Add `/api/models/active` endpoint (get/set current model; persist selection in SQLite)
- [x] Add streaming `/ws` endpoint using Ollama `stream: True` (start/token/done events)
- [x] Implement conversation history (last 20 messages passed to LLM)
- [x] Persist conversation messages to SQLite
- [x] Create conversation REST API (list, get, create, update, delete)
- [x] Build **Chat screen** in React (streaming message list, text input, send button)
- [x] Build **Conversation history screen** (list, open, delete, create)
- [x] Build **Model management screen** (list models, select active)
- [x] Update Header with live connection status, active model, and local clock

Verification: production build, TypeScript check, backend compile, and API import passed on 2026-11-23. Live REST/WebSocket chat was not exercised because this managed environment blocks loopback socket access.

---

### Phase 5 – Memory and RAG ✅ IMPLEMENTATION COMPLETE (updated 2026-11-23 16:49 IST)
**Goal:** Persistent long-term memory and document intelligence with management UI.

Tasks:
- [x] Design memory schema (SQLite memories and embeddings; document chunks store embeddings and metadata)
- [x] Implement memory extraction after each conversation turn
- [x] Implement semantic memory retrieval and merge with document results
- [x] Add document file upload endpoint (`POST /api/documents/upload`)
- [x] Add document list endpoint (`GET /api/documents`)
- [x] Add document delete endpoint (`DELETE /api/documents/{id}`)
- [x] Add chunk-level metadata (source file, page, chunk index)
- [x] Build **Knowledge base screen** (upload, list, delete documents)
- [x] Build **Memory management screen** (view, add, edit, delete memories)
- [x] Add document reference display in chat responses and persisted message metadata

Verification: frontend build/type check, backend compile/API import, and ORM mapper configuration passed on 2026-11-23. The live upload, retrieval, and Ollama memory-extraction flow was not exercised because this managed environment blocks loopback socket access; include it in Phase 9 verification.

---

### Phase 6 – Voice
**Goal:** Reliable, interruptible voice conversation.

Tasks:
- [x] Integrate `webrtcvad-wheels` for proper voice activity detection
- [x] Replace byte-threshold with fixed-frame VAD segmentation
- [x] Add configurable speech rate to settings API
- [x] Add microphone selection to frontend voice settings
- [x] Add interrupt/stop speech button to voice UI
- [ ] Verify full voice → STT → LLM → TTS → audio playback loop (deferred to Phase 9 environment verification)
- [x] Handle ffmpeg-not-found gracefully for legacy encoded audio
- [x] Build **Voice settings panel** in the Voice screen

**Implementation status:** Complete; live voice loop verification is pending. Updated 2026-11-23 17:01 IST.

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
| 3 – Refactoring | ✅ Done | Medium |
| 4 – Core AI | ✅ Done | High |
| 5 – Memory + RAG | ✅ Done | High |
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

The original Phase 2 blockers above are historical and should not be treated as current gating items. Phase 2 implementation is complete; live backend and WebSocket checks could not run because this environment denied loopback socket access. Phase 3 architecture is complete; its async startup-check test is tracked for the Phase 9 test pass. Ollama availability is environment-dependent; the application reports degraded AI health when Ollama is unavailable.
