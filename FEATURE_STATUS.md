# Aurora – Feature Status
**Historical audit baseline:** 2026-11-21
**Current Phase 6 status:** 2026-11-23 17:01 IST

## Current status update — Phases 4–6

This section supersedes the matching historical entries below for features delivered through Phase 4. Live REST/WebSocket operation was not exercised in the loopback-restricted environment; implementation checks (build, type check, compile, import) passed.

| Area | Current status | Notes |
|---|---|---|
| Ollama text generation and streaming | ✅ Implemented | WebSocket streams `start`, `token`, and `done` events through the async Ollama service |
| Active model selection | ✅ Implemented | Lists installed models, validates selection, persists it in SQLite, and restores it at startup |
| Conversation context | ✅ Implemented | Recent messages are loaded from SQLite and included in the prompt |
| Conversation persistence | ✅ Implemented | User and assistant messages persist after each completed response |
| Conversation REST API | ✅ Implemented | List, read, create, update, and delete |
| Chat screen | ✅ Implemented | Streaming response display and message composer |
| Conversation history screen | ✅ Implemented | Opens and deletes conversations; creates new chats |
| Model management screen | ✅ Implemented | Lists local Ollama models and selects the active model |
| Header status | ✅ Implemented | Live backend health indicator, local clock, and active model display |
| Long-term memory embeddings | ✅ Implemented | Stored in SQLite and used for cosine similarity retrieval |
| Automatic memory extraction | ✅ Implemented | Local model extracts durable user facts after a chat turn |
| Document chunk metadata | ✅ Implemented | SQLite stores source filename, page number, chunk index, content, and embedding |
| Knowledge base API and UI | ✅ Implemented | Upload/list/delete for PDF, TXT, and DOCX; 25 MB upload limit |
| Memory management API and UI | ✅ Implemented | List, add, edit, and delete memories |
| Chat document references | ✅ Implemented | Assistant message metadata stores source references; UI shows filename and PDF page when available |
| Voice activity detection | ✅ Implemented | WebRTC VAD segments fixed-size PCM frames with pre-roll and silence endpointing |
| Voice transcription input | ✅ Implemented | Browser AudioWorklet sends 16 kHz mono PCM; normal PCM-to-WAV path does not require FFmpeg |
| Legacy encoded audio decoding | ⚠️ Dependency required | Clear setup error directs users to install FFmpeg if pydub cannot decode an encoded upload |
| Speech output rate | ✅ Implemented | Persisted 100–300 rate setting controls pyttsx3 |
| Microphone selection | ✅ Implemented | Voice settings lets users pick enumerated audio inputs |
| Interruptible voice playback | ✅ Implemented | Stop control halts local playback and signals the backend to suppress stale speech; recording also interrupts playback |
| Full voice pipeline runtime | ⏳ Not verified | Requires installed backend dependencies, a usable microphone, and local Ollama; defer to Phase 9 |

---

## Legend
| Status | Meaning |
|---|---|
| ✅ Working | Implemented and functional (when deps are installed) |
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
