"""
Aurora Backend API — FastAPI + WebSocket
Phase 2: Fixed async blocking, port alignment, conversation history scaffold.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .intent.intent_router import IntentRouter
from .intent.rag_service import RAGService
from .perception.tts import Pyttsx3TTS
from .perception.stt import WhisperSTT

logger = logging.getLogger("aurora.api")

app = FastAPI(title="Aurora Assistant API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.vite_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lazy singletons — initialized once on first use
# ---------------------------------------------------------------------------
_rag: RAGService | None = None
_router: IntentRouter | None = None
_tts: Pyttsx3TTS | None = None
_stt: WhisperSTT | None = None


def get_rag() -> RAGService:
    global _rag
    if _rag is None:
        _rag = RAGService()
    return _rag


def get_router() -> IntentRouter:
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router


def get_tts() -> Pyttsx3TTS:
    global _tts
    if _tts is None:
        _tts = Pyttsx3TTS()
    return _tts


def get_stt() -> WhisperSTT:
    global _stt
    if _stt is None:
        _stt = WhisperSTT()
    return _stt


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------
class Session:
    def __init__(self, session_id: str, ws: WebSocket):
        self.session_id = session_id
        self.ws = ws
        # Conversation history: list of {"role": "user"|"assistant", "content": str}
        self.history: List[Dict[str, str]] = []
        self.last_audio_at: float = 0.0


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    async def connect(self, ws: WebSocket) -> Session:
        await ws.accept()
        sid = str(uuid.uuid4())
        session = Session(sid, ws)
        self._sessions[sid] = session
        return session

    def get(self, sid: str) -> Session | None:
        return self._sessions.get(sid)

    def disconnect(self, sid: str):
        self._sessions.pop(sid, None)


sessions = SessionManager()
_CANCEL_WINDOW_S = 1.5


# ---------------------------------------------------------------------------
# Helpers — all blocking work offloaded to thread pool
# ---------------------------------------------------------------------------
async def run_llm(router: IntentRouter, message: str, context: List[str], history: List[Dict]) -> str:
    """Non-blocking LLM call via asyncio.to_thread."""
    return await asyncio.to_thread(router.route, message, context, history)


async def run_tts(tts: Pyttsx3TTS, text: str) -> bytes | None:
    """Non-blocking TTS synthesis via asyncio.to_thread."""
    return await asyncio.to_thread(tts.synthesize, text)


async def run_stt(stt: WhisperSTT, audio_bytes: bytes) -> str | None:
    """Non-blocking STT transcription via asyncio.to_thread."""
    return await asyncio.to_thread(stt.transcribe_chunk, audio_bytes)


async def run_rag(rag: RAGService, query: str, k: int = 4):
    """Non-blocking RAG retrieval via asyncio.to_thread."""
    return await asyncio.to_thread(rag.retrieve, query, k)


async def process_and_respond(session: Session, user_message: str):
    """Full pipeline: RAG → LLM → TTS → send, all non-blocking."""
    rag = get_rag()
    router = get_router()
    tts = get_tts()

    try:
        # 1. RAG retrieval
        retrieved_pairs = await run_rag(rag, user_message, k=4)
        context = [text for text, _ in retrieved_pairs]

        # 2. LLM generation (passes conversation history)
        answer = await run_llm(router, user_message, context, session.history)

        # 3. Update history
        session.history.append({"role": "user", "content": user_message})
        session.history.append({"role": "assistant", "content": answer})
        # Keep last 20 turns to avoid context overflow
        if len(session.history) > 40:
            session.history = session.history[-40:]

        # 4. Send text response
        await session.ws.send_json({"message": answer})

        # 5. TTS (only if no recent barge-in)
        if tts.is_ready and (time.time() - session.last_audio_at) > _CANCEL_WINDOW_S:
            audio = await run_tts(tts, answer)
            if audio:
                await session.ws.send_bytes(audio)

    except Exception as e:
        logger.error(f"[{session.session_id}] Pipeline error: {e}")
        try:
            await session.ws.send_json({"error": str(e)})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Health check — also verifies Ollama reachability."""
    import httpx
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    return JSONResponse({
        "status": "ok",
        "ollama": ollama_ok,
        "model": settings.ollama_model,
        "version": "0.2.0",
    })


@app.get("/api/models")
async def list_models():
    """List all models available in Ollama."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            r.raise_for_status()
            data = r.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"models": models, "active": settings.ollama_model}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=503)


@app.post("/api/models/select")
async def select_model(payload: dict):
    """Switch the active Ollama model at runtime."""
    model = payload.get("model", "").strip()
    if not model:
        return JSONResponse({"error": "model name required"}, status_code=400)
    settings.ollama_model = model
    # Reset router so it picks up new model
    global _router
    _router = None
    return {"active": settings.ollama_model}


@app.post("/index")
async def rebuild_index():
    """Re-build the FAISS vector store from documents in backend/data/docs/."""
    from .intent.load_documents import load_all_chunks
    rag = get_rag()
    chunks = await asyncio.to_thread(load_all_chunks)
    await asyncio.to_thread(rag.build, chunks)
    return {"chunks": len(chunks)}


# ---------------------------------------------------------------------------
# WebSocket: Chat
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    session = await sessions.connect(websocket)
    logger.info(f"Chat WS connected: {session.session_id}")
    try:
        # Send session_id and personalized greeting
        await websocket.send_json({
            "message": "connected",
            "session_id": session.session_id,
        })
        greeting = f"Welcome back, {settings.user_name}! How can I help you today?"
        await websocket.send_json({"message": greeting})

        tts = get_tts()
        if tts.is_ready:
            audio = await run_tts(tts, greeting)
            if audio:
                await websocket.send_bytes(audio)

        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                user_message = payload.get("message") or raw
            except Exception:
                user_message = raw

            if not user_message.strip():
                continue

            await process_and_respond(session, user_message)

    except WebSocketDisconnect:
        logger.info(f"Chat WS disconnected: {session.session_id}")
        sessions.disconnect(session.session_id)
    except Exception as e:
        logger.error(f"Chat WS error: {e}")
        sessions.disconnect(session.session_id)


# ---------------------------------------------------------------------------
# WebSocket: Audio
# ---------------------------------------------------------------------------
@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id")
    if not session_id:
        await websocket.send_json({"error": "missing session_id"})
        await websocket.close()
        return

    session = sessions.get(session_id)
    if not session:
        await websocket.send_json({"error": "chat session not found"})
        await websocket.close()
        return

    stt = get_stt()
    audio_buffer = bytearray()
    # ~3 seconds of 128kbps audio ≈ 48KB; use 50KB as threshold
    THRESHOLD = 50_000

    logger.info(f"Audio WS connected for session: {session_id}")
    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"]:
                # Mark barge-in time to suppress TTS
                session.last_audio_at = time.time()
                audio_buffer.extend(msg["bytes"])

                if len(audio_buffer) >= THRESHOLD:
                    if stt.is_ready:
                        transcript = await run_stt(stt, bytes(audio_buffer))
                        audio_buffer.clear()
                        if transcript:
                            await websocket.send_json({"transcript": transcript})
                            # Route through full pipeline on the chat session
                            await process_and_respond(session, transcript)
                        else:
                            await websocket.send_json({"transcript": ""})
                    else:
                        audio_buffer.clear()
                        await websocket.send_json({"error": "STT not ready"})

    except WebSocketDisconnect:
        logger.info(f"Audio WS disconnected: {session_id}")
        # Flush remaining buffer
        if audio_buffer and stt.is_ready:
            try:
                transcript = await run_stt(stt, bytes(audio_buffer))
                if transcript:
                    await process_and_respond(session, transcript)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Audio WS error: {e}")
