# Aurora – Development Roadmap
**Created:** 2026-11-21  
**Target:** Aurora 1.0 — Stable, installable, locally hosted AI desktop assistant
**Last Status Update:** 2026-11-27

### Portable release status update — 2026-11-27

PyInstaller ONEDIR remains the active release path. The existing v10 unsigned candidate passed self-check, local Ollama/model handling, native WebSocket, RAG indexing/retrieval, graceful shutdown, restart, and user-data persistence on the development host; its grounded generation failed. An explicit context-grounding prompt fix passed focused tests and cold-cache RAG checks in a rebuilt local v12 ONEDIR. No replacement ZIP was packaged. The full backend suite passed earlier (120 tests; three upstream warnings).

No ZIP has been generated because the checkout is dirty. Official signing is BLOCKED pending authorized external keys and a trusted fingerprint. A clean Windows 10/11 VM, update/rollback, full offline, voice/FFmpeg, and outbound-traffic checks remain NOT TESTED. See `RELEASE_VALIDATION_REPORT.md`; earlier roadmap checkboxes and dated statements remain historical.

---

## Architecture Decision: Python 3.12 Virtual Environment

**Decision:** Create a Python 3.12 virtual environment for the backend.  
**Reason:** Python 3.14.2 is too new for `faiss-cpu`, `openai-whisper`, and `torch` wheels. 3.12 is the most broadly supported version for all ML/AI packages in this stack.  
**Action required from user:** Install Python 3.12 alongside existing 3.14, or use `py -3.12` launcher.

---

## Architecture Decision: Keep React Frontend, Extend Significantly

**Decision:** Keep the existing React + Vite + Tailwind stack. Add all missing screens.  
**Reason:** `VoiceMicOrb.tsx` and the WebSocket hook are genuinely good. Rewriting in Electron or Tauri would delay the project by weeks and add complexity.  
**Desktop packaging:** Use PyInstaller with the Vite production build to bundle the FastAPI service and serve the UI locally. This follows the Phase 10 decision and avoids adding a desktop framework.

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

### Phase 2 – Stabilization ✅ IMPLEMENTATION AND FROZEN RUNTIME VERIFIED (2026-11-28)
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
- [x] Confirm backend startup and WebSocket end-to-end — existing v10 ONEDIR returned healthy API status and completed a browser chat over WebSocket on 2026-11-28
- [x] Import backend API module — passed 2026-11-23
- [x] Frontend production build — passed 2026-11-23 (1476 modules)

---

### Phase 3 – Architecture Refactoring ✅ IMPLEMENTATION COMPLETE; DATABASE AND STARTUP SMOKE VERIFIED (2026-11-28)
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

Verification: all Phase 3 synchronous core/database tests passed (14 passed). The frozen v10 app also passed database health and conversation/memory CRUD checks on 2026-11-28. Internal module boundaries and the historical async startup-check test were not re-tested through the frozen app.

---

### Phase 4 – Core AI Assistant ✅ IMPLEMENTATION AND FROZEN RUNTIME VERIFIED (updated 2026-11-28)
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

Verification: the existing v10 ONEDIR exposed healthy model/conversation APIs; model selection and conversation CRUD passed. Playwright loaded Chat, History, and Models, completed a streamed chat over `/ws`, and showed the persisted conversation on 2026-11-28. Exact 20-message history truncation was not tested.

---

### Phase 5 – Memory and RAG ✅ FROZEN RAG FIX AND MEMORY API VERIFIED (updated 2026-11-28)
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

Verification: v10 indexed and cited a one-chunk document but repeatedly ignored its relevant fact; an intermediate temperature-only v11 change also failed. The final fix adds explicit, injection-aware instructions to answer from relevant excerpts without changing the configured generation temperature. The focused router suite passed (10 tests); rebuilt local v12 ONEDIR indexed with an initially empty Hugging Face cache, downloaded the embedding weights, and returned the fact with its citation on three API queries and one Playwright chat. The existing v10 unsigned ZIP remains unchanged and still has the RAG bug. Memory create/embed/update/delete and semantic retrieval passed on 2026-11-28. Automatic memory extraction after each turn and combined memory-plus-document retrieval remain untested.

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

**Implementation status:** Complete; voice settings and speech-rate API are verified, but microphone capture, enrollment, and the full voice loop remain untested without audio hardware. Updated 2026-11-28.

---

### Phase 7 – Advanced AI ⚠️ PLAN AND CONFIRMATION FLOWS VERIFIED; VOICE AUTH NOT TESTED (updated 2026-11-28)
**Goal:** Voice authentication, agentic tool execution, desktop automation.

Tasks:
- [x] Voice enrollment: record and store local speaker feature vectors
- [x] Voice verification: compare a new sample with the saved profile (approximate match only)
- [x] Tool calling framework: schemas, strict allowlist validation, dispatch, and tool-result injection into a summary
- [x] Implement allowlisted tools: system info, uploaded-file listing, app launch, clipboard read
- [x] Implement model-generated multi-step plans, limited to five allowlisted steps
- [x] Require explicit review and confirmation before executing every plan
- [x] Persist plans, approval state, and redacted execution history in SQLite
- [x] Build **Agent / task management screen** with plan preview, approve/cancel, history, and voice-profile controls

**Verification:** the frozen app listed allowlisted tools, generated and persisted a reviewable plan, rejected execution without confirmation (HTTP 400), and cancelled the plan. No desktop action or voice profile was executed. Voice matching is a convenience feature and must not be used to protect actions or data.

---

### Pre-Phase 8 – Modern Software Development and DevOps ⚠️ CONFIGURED; LIVE WORKFLOWS UNVERIFIED (updated 2026-11-23 17:57 IST)
**Goal:** Make Aurora a practical learning project for team planning, source control, CI/CD, containers, testing, quality, releases, and operations.

Tasks:
- [x] Document manual Jira epics, stories, tasks, bugs, sprint planning/review, estimates, and acceptance criteria; add matching GitHub issue templates
- [x] Document feature/bugfix branches, PR review, protected branches, secrets, and version tags
- [x] Add GitHub Actions workflows for lint, unit/integration, UI/API, Java QA, dependency/security checks, container builds, and release assets
- [x] Replace Jenkins fail-open stages with required checks, test reports, SonarQube gate, build/package, manual staging approval, and rollback procedure
- [x] Containerize the backend and static frontend; add isolated test/E2E profiles, volumes, networking, health checks, and host-managed Ollama
- [x] Add pytest, Playwright, and separate Maven/TestNG/Selenium/REST Assured/Cucumber workflows and examples
- [x] Add SonarQube project and Jenkins scanner configuration
- [x] Add local Prometheus metrics and provisioned Grafana dashboard
- [x] Add staging, checksummed release artifacts, deployment health checks, and rollback scripts
- [ ] Configure Jira/GitHub/Jenkins/SonarQube accounts and credentials on the user's hosts; exercise full CI/staging lifecycle
- [x] Produce the native Windows installer in Phase 10; clean-system validation is tracked as a remaining verification task

**Status:** Workflow and service configuration is present and Compose syntax was validated. `/metrics` responded in the frozen app; live CI/staging lifecycle, external accounts, and credentials were not tested. See the 2026-11-28 verification matrix below.

---

### Phase 8 – UI and UX Polish ✅ PRIMARY INTERACTIONS VERIFIED; SOME POLISH NOT TESTED (updated 2026-11-28)
**Goal:** Premium, dark-themed, polished desktop experience.

Tasks:
- [x] Apply consistent dark theme (black/charcoal backgrounds, cyan/blue accents) and a light theme toggle — both themes switched in Playwright
- [x] Keep responsive side navigation for all eight screens — all eight screens loaded; navigation remained visible at 390px
- [x] Add Framer Motion page and setup-step transitions — screen navigation and all three setup steps completed
- [x] Add live backend/Ollama/database and selected-model status; show browser JS heap only when the browser exposes it — dashboard showed live healthy status, model, and browser heap
- [x] Add first-run wizard for username, installed model selection, and optional voice enrollment — name/model/voice steps displayed; microphone enrollment not attempted
- [~] Replace dashboard sample data and polish shared shell, focus, scrollbar, and reduced-motion styles — live dashboard data verified; focus, scrollbar, and reduced-motion behavior not individually tested
- [x] Add keyboard shortcuts for new chat, screen navigation, help, and dialog dismissal — Ctrl+N, Alt+4, ?, and Escape passed
- [~] Add an error boundary with recovery action — not fault-injected

`[~]` means implementation is present but one or more listed behaviors remain untested. The browser heap metric is not system RAM usage.

**Frozen-app verification:** Existing v10 was tested first; its RAG grounding failure required a minimal source fix, regression test, and v12 ONEDIR rebuild. Per-feature PASS/FAIL/NOT TESTED results and one-line evidence for Phases 2–8, including the pre-Phase 8 DevOps work, are in [RELEASE_VALIDATION_REPORT.md](./RELEASE_VALIDATION_REPORT.md#phases-2-8-frozen-app-verification). The existing v10 unsigned ZIP was not repackaged and does not contain this fix.

---

### Phase 9 – Testing
**Goal:** Test coverage for all critical paths.

**Status:** ⚠️ Coverage added; selected synchronous tests pass. Async/API/WebSocket suites are not verified in this managed Windows environment because local socket-pair creation is blocked. See `DEVELOPMENT_PROGRESS.md`.

Tests and evidence:
- [~] `test_startup.py` plus API health checks — live `/health` smoke passed; async/startup and TestClient tests remain blocked here
- [~] `test_ollama.py` — mocked connectivity/model listing/stream tests authored; async runner blocked here
- [~] `test_websocket.py` — connect, message, and invalid audio-session cases exist; integration runner blocked here
- [~] `test_streaming.py` — mocked incremental stream parser test authored; async runner blocked here
- [x] RAG (`test_rag_service.py`) — 5 retrieval/index tests passed; uses mocked embeddings
- [~] `test_memory.py` — isolated SQLite store/retrieve/update/delete authored; async DB runner blocked here
- [~] `test_database.py` — SQLite CRUD authored; schema/model checks pass; async CRUD blocked here
- [x] `test_tts.py` — generated WAV bytes using a fake OS voice engine; passed
- [x] `test_stt.py` — transcribes generated PCM through a validated WAV fixture and fake recognizer; passed
- [~] `test_voice_auth.py` — 3 embedding tests passed; API enroll/verify/reject lifecycle authored but not run
- [x] `test_tools.py` and `test_agent_tools.py` — allowlist and safety tests passed
- [~] `test_error_handling.py` — corrupt/unsupported-document cases passed; async Ollama failure and WebSocket bad-session checks not run

`[~]` means tests were added or already existed, but full verification is pending. `test_rag_service.py` fulfills the planned RAG coverage filename; WebSocket cases live in `tests/integration/test_websocket.py`.

---

### Phase 10 – Desktop Packaging ⚠️ ONEDIR BUILT; CLEAN-SYSTEM VALIDATION PENDING (updated 2026-11-28)
**Goal:** Installable Windows `.exe`.

**Decision:** Option C — PyInstaller + Vite build, serving the React frontend from FastAPI. The packaged app stores writable files under the user's Local AppData directory.

Tasks:
- [x] Build frontend (`npm run build`; production build passed 2026-11-23)
- [x] Serve frontend static files from FastAPI (static mount smoke check passed)
- [x] Package backend with PyInstaller into single `.exe` — built and launched successfully with local health/static UI checks
- [x] Add the primary PyInstaller ONEDIR portable layout — Windows build and packaged FAISS index/search self-check passed; loopback API smoke remains blocked in this sandbox
- [x] Create Inno Setup installer script — compiled with Inno Setup 7.1.1; temporary install/uninstall smoke passed
- [x] Add application icon
- [x] Create startup/shutdown scripts — PowerShell parser checks passed
- [~] Test installation on clean Windows system — temporary local install/uninstall passed; separate clean account/VM remains pending

The legacy one-file executable previously passed local HTTP checks. The newer ONEDIR build passed its packaged self-check, and local v12 ONEDIR RAG generation passed cold-cache API and browser checks; clean Windows account/VM validation remains pending. See `packaging/README.md` and `RELEASE_VALIDATION_REPORT.md` for evidence and remaining gates.

---

### Phase 11 – Release
**Goal:** Aurora 1.0 release package.

Tasks:
- [x] Write `README.md`
- [ ] Write `INSTALLATION.md`
- [ ] Write `USER_GUIDE.md`
- [x] Write `CHANGELOG.md`
- [~] Build signed portable ZIP and release verifier — ONEDIR/verifier build and verifier smoke passed; signing keys and complete clean-system validation are pending
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
| B4 | Desktop packaging method (Phase 10) | Resolved: PyInstaller + static serve |

The original Phase 2 blockers above are historical and should not be treated as current gating items. Phase 2 implementation is complete; live backend and WebSocket checks could not run because this environment denied loopback socket access. Phase 3 architecture is complete; its async startup-check test is tracked for the Phase 9 test pass. Ollama availability is environment-dependent; the application reports degraded AI health when Ollama is unavailable.
# Portable distribution milestone

**Status (2026-11-23 22:18 IST): Implementation in progress.** PyInstaller ONEDIR spec, build/package/checksum/verification scripts, runtime data layout migration, six passing focused tests, and a Windows ONEDIR build are present. A complete temporary-key ZIP dry run passed package verification and the no-source content audit. A Torch/FAISS duplicate OpenMP runtime abort was found during a combined native runtime trial; local RAG in ONEDIR is not yet validated. Official signed release remains gated on resolving that runtime issue, clean VM tests, updater tests, and developer-controlled signing keys. Current source uses FastAPI/WebSocket and direct FAISS modules; Socket.IO and LangChain are not used and were not introduced as architecture changes.
