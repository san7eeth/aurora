from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict
import uuid
import json
from .intent.rag_service import RAGService
from .intent.intent_router import IntentRouter
from .perception.tts import Pyttsx3TTS
from .perception.stt import WhisperSTT
import time


app = FastAPI(title="Aurora Assistant API")

# Allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections[session_id] = websocket
        return session_id

    def get(self, session_id: str) -> WebSocket | None:
        return self.active_connections.get(session_id)

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)


sessions = SessionManager()
rag = RAGService()
router = IntentRouter()
tts = Pyttsx3TTS()
stt = WhisperSTT()

# Simple barge-in state: if audio arrives, set cancel flag to avoid sending TTS
_tts_cancel: Dict[str, float] = {}
_CANCEL_WINDOW_S = 1.0  # if new audio within last second, skip sending TTS


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    session_id = await sessions.connect(websocket)
    try:
        # On connect, inform client of its session_id
        await websocket.send_json({"message": "connected", "session_id": session_id})
        # Personalized greeting (text + optional audio)
        greeting = "Welcome, Sangeeth! How can I help you today?"
        await websocket.send_json({"message": greeting})
        last_cancel = _tts_cancel.get(session_id, 0.0)
        if tts.is_ready and (time.time() - last_cancel) > _CANCEL_WINDOW_S:
            audio = tts.synthesize(greeting)
            if audio:
                await websocket.send_bytes(audio)
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                user_message = payload.get("message") or raw
            except Exception:
                user_message = raw
            retrieved = [t for t, _ in rag.retrieve(user_message, k=4)]
            answer = router.route(user_message, retrieved)
            await websocket.send_json({"message": answer})
            last_cancel = _tts_cancel.get(session_id, 0.0)
            if tts.is_ready and (time.time() - last_cancel) > _CANCEL_WINDOW_S:
                audio = tts.synthesize(answer)
                if audio:
                    await websocket.send_bytes(audio)
    except WebSocketDisconnect:
        sessions.disconnect(session_id)


@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket):
    # Expect query param session_id
    await websocket.accept()
    session_id = websocket.query_params.get("session_id")
    if not session_id:
        await websocket.send_json({"error": "invalid or missing session_id"})
        await websocket.close()
        return
    chat_ws = sessions.get(session_id)
    if not chat_ws:
        await websocket.send_json({"error": "chat socket not found for session"})
        await websocket.close()
        return

    # Buffer audio bytes and transcribe when large enough
    audio_buffer = bytearray()
    # ~100KB threshold for faster transcription (reduced from 200KB)
    TRANSCRIBE_THRESHOLD = 100_000

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"] is not None:
                # mark possible barge-in
                _tts_cancel[session_id] = time.time()
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                if len(audio_buffer) >= TRANSCRIBE_THRESHOLD:
                    if stt.is_ready:
                        transcript = stt.transcribe_chunk(bytes(audio_buffer))
                        if transcript:
                            # send transcript back on audio socket
                            await websocket.send_json({"transcript": transcript})
                            # auto-route into chat pipeline and send result on chat socket
                            retrieved = [t for t, _ in rag.retrieve(transcript, k=4)]
                            answer = router.route(transcript, retrieved)
                            await chat_ws.send_json({"message": answer})
                            # send TTS on chat socket if not recently cancelled
                            last_cancel = _tts_cancel.get(session_id, 0.0)
                            if tts.is_ready and (time.time() - last_cancel) > _CANCEL_WINDOW_S:
                                audio = tts.synthesize(answer)
                                if audio:
                                    await chat_ws.send_bytes(audio)
                        else:
                            await websocket.send_json({"transcript": "[audio processing failed]"})
                    else:
                        await websocket.send_json({"transcript": "[STT not ready]"})
                    audio_buffer.clear()
            elif "text" in message and message["text"] is not None:
                text = message["text"].strip().lower()
                if text == "flush":
                    if audio_buffer:
                        if stt.is_ready:
                            transcript = stt.transcribe_chunk(bytes(audio_buffer))
                            if transcript:
                                await websocket.send_json({"transcript": transcript})
                                retrieved = [t for t, _ in rag.retrieve(transcript, k=4)]
                                answer = router.route(transcript, retrieved)
                                await chat_ws.send_json({"message": answer})
                                last_cancel = _tts_cancel.get(session_id, 0.0)
                                if tts.is_ready and (time.time() - last_cancel) > _CANCEL_WINDOW_S:
                                    audio = tts.synthesize(answer)
                                    if audio:
                                        await chat_ws.send_bytes(audio)
                            else:
                                await websocket.send_json({"transcript": "[audio processing failed]"})
                        else:
                            await websocket.send_json({"transcript": "[STT not ready]"})
                        audio_buffer.clear()
                else:
                    await websocket.send_json({"transcript": f"[text received: {message['text']}]"})
    except WebSocketDisconnect:
        # Best-effort flush on disconnect
        if audio_buffer:
            try:
                if stt.is_ready:
                    _ = stt.transcribe_chunk(bytes(audio_buffer))
            except Exception:
                pass
        return


@app.post("/index")
async def rebuild_index():
    from .intent.load_documents import load_all_chunks

    chunks = load_all_chunks()
    rag.build(chunks)
    return {"chunks": len(chunks)}


