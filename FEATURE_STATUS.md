# Aurora – Feature Status
**Historical audit baseline:** 2026-11-21
**Current status:** Phase 10 executable and installer built; local package/install smoke passes; clean Windows system test pending, 2026-11-23 19:59 IST

## Current status update — Phases 4–7 and DevOps track

This section supersedes the matching historical entries below for Phases 4–7. Live runtime flows remain unverified where noted; implementation checks are recorded in `DEVELOPMENT_PROGRESS.md`.

| Area | Current status | Notes |
|---|---|---|
| Windows desktop package | 🟡 Built and locally smoke-tested | 358 MB PyInstaller executable and 355 MB Inno Setup installer built; health/static/API and temporary install/uninstall pass; clean account/VM test pending |
| Ollama text generation and streaming | 🧩 Built; runtime verification varies | WebSocket streams `start`, `token`, and `done` events through the async Ollama service |
| Active model selection | 🧩 Built; runtime verification varies | Lists installed models, validates selection, persists it in SQLite, and restores it at startup |
| Conversation context | 🧩 Built; runtime verification varies | Recent messages are loaded from SQLite and included in the prompt |
| Conversation persistence | 🧩 Built; runtime verification varies | User and assistant messages persist after each completed response |
| Conversation REST API | 🧩 Built; runtime verification varies | List, read, create, update, and delete |
| Chat screen | 🧩 Built; runtime verification varies | Streaming response display and message composer |
| Conversation history screen | 🧩 Built; runtime verification varies | Opens and deletes conversations; creates new chats |
| Model management screen | 🧩 Built; runtime verification varies | Lists local Ollama models and selects the active model |
| Header status | 🧩 Built; runtime verification varies | Live backend health indicator, local clock, and active model display |
| Long-term memory embeddings | 🧩 Built; runtime verification varies | Stored in SQLite and used for cosine similarity retrieval |
| Automatic memory extraction | 🧩 Built; runtime verification varies | Local model extracts durable user facts after a chat turn |
| Document chunk metadata | 🧩 Built; runtime verification varies | SQLite stores source filename, page number, chunk index, content, and embedding |
| Knowledge base API and UI | 🧩 Built; runtime verification varies | Upload/list/delete for PDF, TXT, and DOCX; 25 MB upload limit |
| Memory management API and UI | 🧩 Built; runtime verification varies | List, add, edit, and delete memories |
| Chat document references | 🧩 Built; runtime verification varies | Assistant message metadata stores source references; UI shows filename and PDF page when available |
| Voice activity detection | 🧩 Built; runtime verification varies | WebRTC VAD segments fixed-size PCM frames with pre-roll and silence endpointing |
| Voice transcription input | 🧩 Built; runtime verification varies | Browser AudioWorklet sends 16 kHz mono PCM; normal PCM-to-WAV path does not require FFmpeg |
| Legacy encoded audio decoding | ⚠️ Dependency required | Clear setup error directs users to install FFmpeg if pydub cannot decode an encoded upload |
| Speech output rate | 🧩 Built; runtime verification varies | Persisted 100–300 rate setting controls pyttsx3 |
| Microphone selection | 🧩 Built; runtime verification varies | Voice settings lets users pick enumerated audio inputs |
| Interruptible voice playback | 🧩 Built; runtime verification varies | Stop control halts local playback and signals the backend to suppress stale speech; recording also interrupts playback |
| Full voice pipeline runtime | ⏳ Not verified | Requires installed backend dependencies, a usable microphone, and local Ollama; defer to Phase 9 |
| Voice profile enrollment | 🧩 Built; runtime verification varies | Stores a compact local speaker feature vector; raw audio is not retained |
| Voice profile matching | ⚠️ Approximate | Local similarity match only; not suitable for authentication or access control |
| Agent tool schemas and dispatch | 🧩 Built; runtime verification varies | Strict allowlist and argument validation; no arbitrary shell or filesystem paths |
| Safe local tools | 🧩 Built; runtime verification varies | System info, uploaded file names/sizes, fixed Windows app allowlist, clipboard text |
| Multi-step task planning | 🧩 Built; runtime verification varies | Local model plans up to five allowlisted steps; results feed a final summary |
| Confirmation UI | 🧩 Built; runtime verification varies | Every plan is previewed and requires explicit approval; pending plans can be cancelled |
| Agent execution history | 🧩 Built; runtime verification varies | SQLite persists plans/outcomes; clipboard content is redacted from saved history |
| Agent/task management screen | 🧩 Built; runtime verification varies | Plan creation/review, approval/cancel, history, and voice-profile controls |
| Phase 7 runtime verification | ⏳ Not verified | Requires configured dependencies and local Ollama; defer to Phase 9 |
| Jira workflow | ✅ Documented | Manual Scrum project, epics/stories/tasks/bugs/sprints/points/reviews; no API integration |
| Git/GitHub workflow | ⚠️ Configured; unverified | Branch/review/secrets guidance, issue templates, PR template, CI and release workflows; host branch rules and workflow runs not verified |
| Jenkins CI/CD | ⚠️ Configured; unverified | Required test/security stages, reports, SonarQube, package, manual staging, health check; pipeline not run |
| Docker Compose environment | ⚠️ Configured; syntax checked | Backend/frontend, QA profiles, health checks, persistent volumes, host-managed Ollama; services not started as part of this verification |
| Python automated QA | ⚠️ Test scaffolding present; not run | Pytest unit/integration scaffolding with mocked external services |
| Browser UI/API QA | ⚠️ Test scaffolding present; not run | Playwright Chromium smoke suite in Docker/CI |
| Java QA learning module | ⚠️ Configured; compile/test unverified | Maven/TestNG, Selenium Page Object, REST Assured, Cucumber, Extent reports; local Maven invocation denied |
| SonarQube quality gate | ✅ Configured | Jenkins scanner stage and project configuration; requires local server/token setup |
| Monitoring dashboard | ⚠️ Configured; runtime unverified | `/metrics`, Prometheus scrape config, provisioned Grafana overview dashboard |
| Staging and rollback | ⚠️ Configured; runtime unverified | Manual deploy approval, health verification, PowerShell/Bash rollback helpers |
| Native Windows installer | 🟡 Phase 10 package built and tested locally | Clean Windows account/VM, WebSocket/voice and first-run model tests remain |
| DevOps live execution | ⏳ Not verified | Requires Jira/GitHub/Jenkins credentials and local Docker/CI setup |
| Phase 8 responsive shell/navigation | ⚠️ Built; interaction unverified | Eight-screen navigation and route transitions; lint/type/build passed, browser viewport checks pending |
| First-run setup | ⚠️ Built; runtime unverified | Name/model/optional voice profile; requires backend and microphone for enrollment |
| Dashboard status panel | ⚠️ Built; live data unverified | Backend/Ollama/database/model; JS heap estimate only if browser exposes it, not system RAM |
| Keyboard shortcuts and error boundary | ⚠️ Built; interaction unverified | Shortcut listeners and recovery UI compile; no browser interaction checks run |
| Phase 9 synchronous test subset | ✅ Verified | 55 passed; RAG suite separately passed 5 tests; Python compile, Flake8, and Bandit passed |
| Phase 9 async/API/WebSocket suites | ⏳ Not verified | This managed Windows sandbox blocks event-loop socket-pair startup; run in socket-enabled CI |
| Pre-packaging app runtime | ✅ Verified | FastAPI health and core GET endpoints passed; Vite root returned HTTP 200 using an isolated session database |

---

## Legend
| Status | Meaning |
|---|---|
| ✅ Verified | Relevant automated or manual behavior checks passed; cite evidence in progress log |
| ⚠️ Partial | Implemented but has bugs, missing pieces, or is UI-only |
| ❌ Broken | Implemented but definitely broken |
| 🔲 Not Implemented | Mentioned in design but no code exists |
| 🗑️ Unnecessary | Exists but should be removed |

---

## Backend Features

### AI Engine
| Feature | Status | Notes |
|---|---|---|
| Ollama LLM integration | ⚠️ Partial | Works but synchronous `requests.post()` blocks async event loop |
| Streaming responses | ❌ Broken | `stream: False` hardcoded — no streaming at all |
| Multiple model support | ❌ Broken | Model hardcoded in config — no switching API |
| Model selection via UI | 🔲 Not Implemented | — |
| Conversation context (history) | ❌ Broken | Each turn is fully stateless |
| System prompt configuration | ⚠️ Partial | Hardcoded in `intent_router.py` |
| Temperature / generation params | ⚠️ Partial | Hardcoded in `intent_router.py` |
| Stop generation | 🔲 Not Implemented | — |
| Error handling (Ollama unavailable) | ⚠️ Partial | `requests` raises exception; not gracefully handled to client |
| Model loading/unloading management | 🔲 Not Implemented | — |
| Active model display | 🔲 Not Implemented | — |

### Memory System
| Feature | Status | Notes |
|---|---|---|
| Conversation history (in-turn) | ❌ Broken | Not passed to LLM |
| Persistent conversation storage | 🔲 Not Implemented | No database |
| Long-term semantic memory | 🔲 Not Implemented | — |
| Memory summarization | 🔲 Not Implemented | — |
| Memory management UI | 🔲 Not Implemented | — |
| Edit/delete memories | 🔲 Not Implemented | — |

### RAG Knowledge Base
| Feature | Status | Notes |
|---|---|---|
| PDF ingestion | ✅ Working | `pypdf` via `load_documents.py` |
| TXT ingestion | ✅ Working | Plain read |
| DOCX ingestion | ✅ Working | `python-docx` |
| Text chunking | ✅ Working | Sentence-based, ~400 word windows |
| Embedding generation | ✅ Working | `all-MiniLM-L6-v2` via sentence-transformers |
| FAISS vector store | ✅ Working | `IndexFlatIP`, save/load implemented |
| Retrieval (top-k) | ✅ Working | Cosine similarity search |
| RAG-grounded answers | ⚠️ Partial | Context passed to LLM but no citation/reference tracking |
| Document upload API | ❌ Broken | POST /index triggers re-index but no file upload endpoint |
| Document management API | 🔲 Not Implemented | — |
| Remove document + embeddings | 🔲 Not Implemented | — |
| Corrupted file handling | ⚠️ Partial | pypdf may throw; no graceful error |

### Voice Processing
| Feature | Status | Notes |
|---|---|---|
| Speech-to-text (Whisper) | ⚠️ Partial | Code exists; requires ffmpeg (not installed) and Python 3.14 compat |
| Text-to-speech (pyttsx3) | ⚠️ Partial | Code exists; requires pywin32 (not installed); BLOCKS async loop |
| Voice activation (wake word) | 🔲 Not Implemented | — |
| Microphone selection | 🔲 Not Implemented | — |
| Voice conversation mode | ⚠️ Partial | VoiceView exists but backend port mismatch breaks it |
| Interrupt speech playback | ⚠️ Partial | Barge-in cancel flag exists but unreliable |
| Adjustable speech speed | ⚠️ Partial | Rate hardcoded at 200 in `tts.py` |
| Voice Activity Detection (VAD) | ❌ Broken | 100KB byte threshold — not real VAD |
| Audio device error handling | ⚠️ Partial | MediaDevices errors caught in VoiceMicOrb |

### Voice Authentication
| Feature | Status | Notes |
|---|---|---|
| User voice enrollment | 🔲 Not Implemented | — |
| Voice verification | 🔲 Not Implemented | — |
| Voice profile storage | 🔲 Not Implemented | — |
| Authentication status | 🔲 Not Implemented | — |

### Agentic / Tool Calling
| Feature | Status | Notes |
|---|---|---|
| Tool calling framework | 🔲 Not Implemented | — |
| Task planning | 🔲 Not Implemented | — |
| Multi-step execution | 🔲 Not Implemented | — |
| Desktop automation | 🔲 Not Implemented | — |
| File/folder operations | 🔲 Not Implemented | — |
| App launching | 🔲 Not Implemented | — |
| System information | 🔲 Not Implemented | — |

### Database / Storage
| Feature | Status | Notes |
|---|---|---|
| SQLite database | 🔲 Not Implemented | — |
| Conversation persistence | 🔲 Not Implemented | — |
| Message storage | 🔲 Not Implemented | — |
| Memory storage | 🔲 Not Implemented | — |
| Document metadata | 🔲 Not Implemented | — |
| User preferences | 🔲 Not Implemented | — |
| Settings storage | 🔲 Not Implemented | — |

---

## Frontend Features

### UI / Screens
| Feature | Status | Notes |
|---|---|---|
| Main AI chat screen | ❌ Broken | Hook exists; no input/output UI rendered |
| Dashboard screen | ⚠️ Partial | Renders but all data hardcoded/fake; wrong username |
| Voice assistant screen | ⚠️ Partial | Renders; broken due to port mismatch |
| Conversation history screen | 🔲 Not Implemented | — |
| Memory management screen | 🔲 Not Implemented | — |
| Knowledge base screen | 🔲 Not Implemented | — |
| Model management screen | 🔲 Not Implemented | — |
| Agent / task management screen | 🔲 Not Implemented | — |
| Settings screen | 🔲 Not Implemented | — |
| System status screen | 🔲 Not Implemented | — |

### UX / Design
| Feature | Status | Notes |
|---|---|---|
| Dark mode | ⚠️ Partial | Toggle exists but defaults to light; design intent is dark |
| Light/dark theme | ✅ Working | CSS transitions implemented correctly |
| Animated orb | ✅ Working | Mouse tracking, hover states |
| Waveform visualization | ✅ Working | Real WebAudio analyser data |
| Connection status display | ❌ Broken | Status dot in Header always grey |
| Responsive layout | ✅ Working | Tailwind responsive classes |
| Smooth animations | ✅ Working | Framer Motion + CSS transitions |

### Infrastructure
| Feature | Status | Notes |
|---|---|---|
| Dual WebSocket (chat + audio) | ✅ Working | Well-implemented |
| Binary audio playback (WebAudio) | ✅ Working | ArrayBuffer decoding |
| Browser TTS fallback | ✅ Working | speechSynthesis fallback |
| Session ID management | ✅ Working | Received from server on connect |

---

## Unnecessary / To Remove

| Item | Reason |
|---|---|
| `aurora.py` (root stub) | Misleading; only prints placeholder; real entry point is `app/main.py` |
| `frontend/.bolt/` directory | Bolt.new IDE artifact; not part of the application |
| `backend/package-lock.json` | 92-byte file; appears to be an empty lockfile — no backend Node.js packages |
