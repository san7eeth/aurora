# Aurora – Current Architecture
**As-found state at time of audit: 2026-11-21**

---

## Current System Map

```
Aurora/
├── backend/                       FastAPI + WebSocket server
│   ├── aurora.py                  STUB — does not start the server
│   ├── requirements.txt           Python dependencies (NOT installed)
│   └── app/
│       ├── config.py              Pydantic settings (hardcoded defaults)
│       ├── main.py                Real entry point: uvicorn on port 8000
│       ├── api.py                 FastAPI app — /health, /ws, /ws/audio, /index
│       ├── intent/
│       │   ├── intent_router.py   Calls Ollama /api/generate (BLOCKING, synchronous)
│       │   ├── rag_service.py     FAISS IndexFlatIP + sentence-transformers
│       │   └── load_documents.py  PDF/DOCX/TXT → sentence-chunked strings
│       └── perception/
│           ├── stt.py             Whisper tiny — transcribes 100KB audio chunks
│           └── tts.py             pyttsx3 — synthesizes WAV bytes (BLOCKING)
└── frontend/                      React 18 + Vite + Tailwind + Framer Motion
    └── src/
        ├── App.tsx                Root: Dashboard ↔ Voice view toggle + dark mode
        ├── hooks/
        │   └── useAssistantSocket.ts   Dual WS (chat /ws + audio /ws/audio)
        └── components/
            ├── Header.tsx         Static header with hardcoded date
            ├── DashboardView.tsx  Fake static dashboard (hardcoded "Ayoub")
            ├── VoiceView.tsx      Voice interface — renders VoiceMicOrb
            ├── VoiceMicOrb.tsx    Mic recording + waveform + sends audio chunks
            └── AIOrb.tsx          Decorative animated orb (dashboard CTA)
```

---

## Current Data Flow (As-Built)

### Text Path (designed but NOT exposed in UI)
```
[No text input UI exists] → WS /ws → RAGService.retrieve(k=4) 
  → IntentRouter.route() → [BLOCKS EVENT LOOP] → requests.post(Ollama) 
  → answer text → WS send_json → frontend 
  → [BLOCKS EVENT LOOP] → pyttsx3.synthesize() → WS send_bytes → WebAudio playback
```

### Voice Path (partially working)
```
VoiceMicOrb (1s chunks, 128kbps webm/opus) → WS /ws/audio?session_id=X 
  → buffer until 100KB → WhisperSTT.transcribe_chunk() 
  → [same text path above]
```

### RAG Index Build (manual HTTP call required)
```
POST /index → load_all_chunks() → RAGService.build() 
  → SentenceTransformer.encode() → faiss.IndexFlatIP → saved to data/vectorstore/
```

---

## Runtime Ports

| Service | Port | Status |
|---|---|---|
| FastAPI backend | 8000 | Backend not running |
| Vite dev server | 5173 | Not started |
| Frontend WS target | **8001** | ❌ Port mismatch — frontend points to wrong port |
| Ollama | 11434 | Not running at time of audit |

---

## Dependencies (Required vs Installed)

### Backend
| Package | Required | Installed | Notes |
|---|---|---|---|
| fastapi | ✅ | ❌ | Not installed |
| uvicorn[standard] | ✅ | ❌ | Not installed |
| faiss-cpu | ✅ | ❌ | Python 3.14 wheel may not exist |
| sentence-transformers | ✅ | ❌ | Not installed |
| openai-whisper | ✅ | ❌ | Python 3.14 wheel may not exist |
| pyttsx3 | ✅ | ❌ | Not installed |
| pywin32 | ✅ | ❌ | Not installed |
| pydub | ✅ | ❌ | Not installed |
| pypdf | ✅ | ❌ | Not installed |
| python-docx | ✅ | ❌ | Not installed |
| requests | ✅ | ❌ | Not installed |
| pydantic-settings | ✅ | ❌ | Not installed |
| ffmpeg | ✅ | ❌ | System dependency — not in PATH |

### Frontend
| Package | Required | Installed |
|---|---|---|
| react, react-dom | ✅ | ❌ (node_modules missing) |
| framer-motion | ✅ | ❌ |
| lucide-react | ✅ | ❌ |
| tailwindcss, vite | ✅ | ❌ |

---

## Missing Screens / Features (Frontend)

| Screen | Exists | Notes |
|---|---|---|
| Text Chat | ❌ | Hook exists but no UI |
| Conversation History | ❌ | — |
| Memory Management | ❌ | — |
| Knowledge Base / RAG | ❌ | — |
| Model Management | ❌ | — |
| Agent / Task Management | ❌ | — |
| Settings | ❌ | — |
| System Status | ❌ | — |
| Dashboard | ⚠️ | Static fake data |
| Voice | ⚠️ | Rendered but broken (port mismatch) |

---

## Missing Backend Services

| Service | Exists | Notes |
|---|---|---|
| Conversation history store | ❌ | — |
| Persistent SQLite database | ❌ | — |
| Long-term memory (semantic) | ❌ | — |
| Streaming LLM responses | ❌ | Ollama called with stream=False |
| Model listing API | ❌ | — |
| Model switching API | ❌ | — |
| Document upload endpoint | ❌ | Only POST /index (manual CLI trigger) |
| Document management API | ❌ | — |
| Memory management API | ❌ | — |
| Settings API | ❌ | — |
| System status API | ❌ | — |
| Voice authentication | ❌ | — |
| Agentic tool calling | ❌ | — |
