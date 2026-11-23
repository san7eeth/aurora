# Aurora – Project Audit Report
**Audit Date:** 2026-11-21  
**Auditor:** Antigravity (AI Dev Agent)  
**Scope:** Complete inspection of all source files, dependencies, environment, architecture, and runtime state.

---

## 1. Environment Findings

| Item | Discovered | Required / Notes |
|---|---|---|
| Python | **3.14.2** | `requirements.txt` targets 3.10–3.12 — **version mismatch** |
| Node.js | 24.21.0 | ✅ Fine |
| npm | 11.19.0 | ✅ Fine |
| NVIDIA Driver | 577.00 | ✅ Fine |
| CUDA | 12.9 | ✅ Fine |
| GPU | RTX 3050 Laptop (4096 MiB) | 255 MiB currently used |
| Ollama | **Not reachable** | Service not running at time of audit |
| ffmpeg | **Not found in PATH** | Required for Whisper STT via pydub — **missing** |
| Virtual environment | **None** | No `.venv` folder in project — deps not installed |
| Installed Python packages | Django, DRF, openpyxl, marshmallow | **None of the Aurora backend deps are installed** |

> **Critical:** The global Python environment has zero Aurora-related packages installed. The backend has never been run in this environment.

---

## 2. Repository State

- **Git history:** 2 commits (`initial commit`, `second`) — essentially a first draft
- **No `.env` files** — all config is in source (`config.py`) with hardcoded defaults
- **No test files** — zero test coverage
- **No virtual environment** — backend deps must be installed before any run
- **No `data/` directory** — `backend/data/docs/` and `vectorstore/` don't exist yet
- **No build artifacts** — frontend `node_modules/` not installed

---

## 3. File-by-File Audit

### Backend Files

| File | Lines | Status | Issues |
|---|---|---|---|
| `aurora.py` | 11 | ⚠️ Stub | Runs `main()` which just prints a placeholder string — the actual server entry in `app/main.py` is separate and correctly references `app/api.py`. This file is misleading and useless. |
| `app/main.py` | 9 | ✅ Correct | Valid uvicorn runner; the real entry point |
| `app/config.py` | 13 | ⚠️ Partial | No `.env` support; hardcoded defaults; CORS origin list not unified |
| `app/api.py` | ~200 | ⚠️ Partially Working | See detailed notes below |
| `app/intent/intent_router.py` | 42 | ⚠️ Partially Working | No conversation history; no streaming; timeout=30s blocks async loop |
| `app/intent/rag_service.py` | 60 | ✅ Working | Solid FAISS + sentence-transformers impl |
| `app/intent/load_documents.py` | 55 | ✅ Working | PDF/DOCX/TXT chunking — functional |
| `app/perception/stt.py` | 100 | ⚠️ Partially Working | Whisper `tiny` loads fine; depends on `ffmpeg` which is not installed; fallback raw-WAV path may fail |
| `app/perception/tts.py` | 55 | ✅ Working | pyttsx3 on Windows — functional once deps installed |

#### `api.py` Detailed Issues

1. **Blocking sync call in async context**: `IntentRouter.route()` calls `requests.post()` (synchronous) inside an `async` WebSocket handler — this **blocks the entire event loop** during every LLM inference.
2. **Blocking TTS**: `tts.synthesize()` calls `pyttsx3.runAndWait()` (synchronous) inside async WebSocket handler — same blocking problem.
3. **Audio buffer threshold is a rough hack**: 100KB byte count with no VAD; real speech will be cut mid-sentence or delayed.
4. **TTS cancel logic is unreliable**: `_tts_cancel` global dict with float timestamps — not thread-safe with asyncio; `_CANCEL_WINDOW_S = 1.0` is arbitrary.
5. **Hardcoded greeting**: `"Welcome, Sangeeth!"` — not configurable.
6. **No session persistence**: Sessions are in-memory dict; a server restart loses all sessions.
7. **No conversation history**: Each `/ws` message is completely stateless.
8. **No streaming**: Entire LLM response buffered before sending.
9. **Port conflict**: `vite.config.ts` sets VITE_WS_BASE to `ws://localhost:8001` but `main.py` starts server on port `8000` — **port mismatch**.

---

### Frontend Files

| File | Lines | Status | Issues |
|---|---|---|---|
| `App.tsx` | 72 | ⚠️ Partial | Only two views: Dashboard and Voice. No Chat view, no Settings, no Memory, no Knowledge Base. Dark mode toggle defaults to `false` (light mode — contradicts design intent of dark theme). |
| `Header.tsx` | 60 | ⚠️ Stub | Hardcoded date `"Thursday 11, 2024"`. Sparkles button does nothing. Status dot is always grey (never shows connection state). |
| `DashboardView.tsx` | 150 | ⚠️ Stub / Demo | Hardcoded user `"Ayoub"` (not `Sangeeth`). All data is static/fake: calendar events, tasks, vacation days. No real data connection. |
| `VoiceView.tsx` | 65 | ⚠️ Partially Working | Renders correctly. isSpeaking timer is a character-count estimate (not actual audio duration). No text chat fallback. |
| `VoiceMicOrb.tsx` | 350 | ✅ Working | Well-implemented mic recording with WebAudio analyser, MediaRecorder, 1s chunks, waveform visualization. Best file in the codebase. |
| `AIOrb.tsx` | 120 | ✅ Working | Mouse-tracking orb with hover states. Purely decorative. |
| `hooks/useAssistantSocket.ts` | 130 | ⚠️ Partially Working | Dual WebSocket (chat + audio) correctly implemented. Browser TTS fallback works. Binary audio playback via WebAudio API works. Bug: `sendMessage()` exposed from hook but no UI text input exists to call it — the chat interface is entirely absent. |

---

## 4. Architectural Problems

### Critical

| # | Problem | Impact |
|---|---|---|
| C1 | Synchronous `requests.post()` to Ollama called inside `async` handler | Blocks entire event loop; will time out under any load |
| C2 | Synchronous `pyttsx3.runAndWait()` inside async WebSocket handler | Same; audio synthesis blocks all connections |
| C3 | Port mismatch: backend on `8000`, frontend hardcoded to `8001` | WebSocket connection always fails without manual fix |
| C4 | No Python virtualenv; backend dependencies not installed | Backend cannot start |
| C5 | ffmpeg not in PATH | Whisper STT cannot convert audio; will silently fall back to raw WAV, likely failing |
| C6 | Python 3.14.2 vs requirements targeting 3.10–3.12 | Several packages (esp. `faiss-cpu`, `openai-whisper`) may not have 3.14 wheels |

### Major

| # | Problem | Impact |
|---|---|---|
| M1 | No conversation history | LLM has zero memory across turns |
| M2 | No text chat UI | The chat hook exists but no input or message list is rendered |
| M3 | `aurora.py` is a stub placeholder, not the real entry point | Confusion about how to start the backend |
| M4 | Hardcoded username "Ayoub" in Dashboard | Wrong user, not configurable |
| M5 | No persistent storage (no SQLite, no DB) | Nothing survives a restart |
| M6 | No `.env` file support | Secrets/config must be changed in source code |
| M7 | Static dashboard data | No real API calls; all cards are fake |

### Minor

| # | Problem | Impact |
|---|---|---|
| m1 | Hardcoded date in Header | Always shows "Thursday 11, 2024" |
| m2 | `package.json` name is `vite-react-typescript-starter` | Should be `aurora` |
| m3 | isSpeaking timer is character-count estimate | May mis-animate the orb |
| m4 | No loading/error state in frontend for WS disconnect | Poor UX on backend failure |
| m5 | `.bolt/prompt` and `.bolt/config.json` are Bolt.new IDE artifacts | Should be removed from production |

---

## 5. Security and Configuration Issues

| Issue | Severity |
|---|---|
| Config hardcoded in `config.py` with no `.env` support | Medium |
| No authentication on any API endpoint | Low (local only) |
| No input sanitization on WebSocket messages before passing to LLM | Low |
| `.bolt/` IDE artifacts committed to repo | Low |
| `allow_credentials=True` with wildcard methods in CORS | Low (local only) |

---

## 6. What Can Be Reused

| Component | Reuse Decision | Rationale |
|---|---|---|
| `rag_service.py` | ✅ Keep + extend | Clean FAISS implementation |
| `load_documents.py` | ✅ Keep + extend | Solid chunking; add metadata support |
| `VoiceMicOrb.tsx` | ✅ Keep | Best-implemented file in the project |
| `AIOrb.tsx` | ✅ Keep | Good animation component |
| `config.py` | ✅ Refactor | Add `.env` support via `python-dotenv` |
| `intent_router.py` | ⚠️ Refactor | Fix blocking call; add history; add streaming |
| `api.py` | ⚠️ Refactor | Fix async blocking; add all new endpoints |
| `stt.py` / `tts.py` | ⚠️ Keep + fix | Functional once deps + ffmpeg are present |
| `DashboardView.tsx` | ⚠️ Replace | Hardcoded fake data; needs real design |
| `Header.tsx` | ⚠️ Extend | Add real clock, connection status |
| `aurora.py` | ❌ Remove or repurpose | Misleading stub |

---

## 7. Summary Scores

| Dimension | Score | Notes |
|---|---|---|
| Backend completeness | 25% | Core pipeline exists but broken and unbuildable |
| Frontend completeness | 20% | UI shell exists but missing all functional screens |
| Test coverage | 0% | No tests whatsoever |
| Documentation | 5% | Minimal inline comments only |
| Production readiness | 0% | Cannot build, run, or deploy |
