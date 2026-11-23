"""
Aurora Backend API — FastAPI + WebSocket
Phase 3: Architecture refactoring — service layer, database, streaming, REST endpoints.
"""

import asyncio
import json
import logging
import sys
import time
import threading
import uuid
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .config import settings
from .core.exceptions import (
    AuroraError,
    NotFoundError,
    OllamaUnavailableError,
    ValidationError,
)
from .core.health import run_startup_checks, startup_state
from .core.logging_config import configure_logging
from .core.runtime_paths import find_frontend_dist
from .services.ollama_service import OllamaService
from .services.conversation_service import ConversationService
from .services.memory_service import MemoryService
from .services.document_service import DocumentService
from .services.settings_service import SettingsService
from .services.agent_service import AgentService
from .agent.tools import TOOL_SCHEMAS, SENSITIVE_TOOLS, execute_tool, validate_arguments
from .perception.voice_auth import voice_embedding, similarity
from .intent.intent_router import IntentRouter
from .perception.tts import Pyttsx3TTS
from .perception.stt import WhisperSTT
from .perception.vad import BYTES_PER_FRAME, VoiceActivityDetector

if TYPE_CHECKING:
    from .intent.rag_service import RAGService

logger = logging.getLogger("aurora.api")

# ---------------------------------------------------------------------------
# Service singletons
# ---------------------------------------------------------------------------
ollama_svc = OllamaService()
conv_svc = ConversationService()
memory_svc = MemoryService()
doc_svc = DocumentService()
settings_svc = SettingsService()
agent_svc = AgentService()


# ---------------------------------------------------------------------------
# Lazy singletons for heavy-init modules (RAG, TTS, STT)
# ---------------------------------------------------------------------------
_rag: "RAGService | None" = None
_router: IntentRouter | None = None
_tts: Pyttsx3TTS | None = None
_stt: WhisperSTT | None = None
_speech_rate = 200
_rag_lock = threading.Lock()
_agent_execution_lock = asyncio.Lock()
_request_count = 0
_request_error_count = 0
_request_duration_seconds = 0.0


def get_rag() -> "RAGService":
    global _rag
    if _rag is None:
        with _rag_lock:
            if _rag is None:
                from .intent.rag_service import RAGService
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
        _tts = Pyttsx3TTS(rate=_speech_rate)
    return _tts


def get_stt() -> WhisperSTT:
    global _stt
    if _stt is None:
        _stt = WhisperSTT()
    return _stt


# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure logging, create the database, and ping Ollama."""
    configure_logging(level=settings.log_level, json_logs=settings.log_json)
    logger.info("Aurora starting up...")
    await run_startup_checks(ollama_svc)
    if startup_state.database == "ok":
        try:
            saved_model = await settings_svc.get("active_model")
            if saved_model:
                settings.ollama_model = str(saved_model)
        except Exception:
            logger.exception("Could not load the saved active model; using configured default")
        try:
            global _speech_rate
            _speech_rate = max(100, min(300, int(await settings_svc.get("speech_rate", 200))))
        except (TypeError, ValueError):
            _speech_rate = 200
    yield
    logger.info("Aurora shutting down...")


# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------
app = FastAPI(title="Aurora Assistant API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.vite_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def collect_request_metrics(request: Request, call_next):
    global _request_count, _request_error_count, _request_duration_seconds
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        _request_count += 1
        _request_error_count += 1
        _request_duration_seconds += time.perf_counter() - started
        raise
    _request_count += 1
    if response.status_code >= 500:
        _request_error_count += 1
    _request_duration_seconds += time.perf_counter() - started
    return response


@app.exception_handler(AuroraError)
async def aurora_error_handler(_request, exc: AuroraError):
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


# ---------------------------------------------------------------------------
# Session manager (in-memory WS sessions, linked to DB conversations)
# ---------------------------------------------------------------------------
class Session:
    def __init__(
        self,
        session_id: str,
        ws: WebSocket,
        conversation_id: str | None = None,
        mode: str = "voice",
    ):
        self.session_id = session_id
        self.ws = ws
        self.conversation_id = conversation_id
        self.mode = mode
        self.history: List[Dict[str, str]] = []
        self.last_audio_at: float = 0.0
        self.speech_generation: int = 0
        self.response_lock = asyncio.Lock()


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    async def connect(
        self, ws: WebSocket, conversation_id: str | None = None, mode: str = "voice"
    ) -> Session:
        await ws.accept()
        sid = str(uuid.uuid4())

        # Create or resume a database conversation
        if conversation_id:
            conv = await conv_svc.get_conversation(conversation_id)
            if not conv:
                conversation_id = None

        if not conversation_id:
            conv = await conv_svc.create_conversation(
                title="New Conversation",
                model_name=settings.ollama_model,
            )
            conversation_id = conv.id

        session = Session(sid, ws, conversation_id, mode)

        # Load recent history from DB
        history = await conv_svc.get_recent_history(conversation_id, n_messages=20)
        session.history = history

        self._sessions[sid] = session
        return session

    def get(self, sid: str) -> Session | None:
        return self._sessions.get(sid)

    def disconnect(self, sid: str):
        self._sessions.pop(sid, None)


sessions = SessionManager()
_CANCEL_WINDOW_S = 1.5
_background_tasks: set[asyncio.Task] = set()


# ---------------------------------------------------------------------------
# Pipeline helpers — all blocking work offloaded to thread pool
# ---------------------------------------------------------------------------
async def run_llm(router: IntentRouter, message: str, context: List[str], history: List[Dict]) -> str:
    return await asyncio.to_thread(router.route, message, context, history)


async def run_tts(tts: Pyttsx3TTS, text: str) -> bytes | None:
    return await asyncio.to_thread(tts.synthesize, text)


async def run_stt(stt: WhisperSTT, audio_bytes: bytes) -> str | None:
    return await asyncio.to_thread(stt.transcribe_chunk, audio_bytes)


async def retrieve_context(query: str, k: int = 4):
    """Retrieve cited document chunks and semantically related saved memories."""
    rag = await asyncio.to_thread(get_rag)
    query_vector = (await asyncio.to_thread(rag.embed_texts, [query]))[0]
    documents = await asyncio.to_thread(rag.retrieve_vector_with_metadata, query_vector, k)
    query_vector = query_vector.tolist()
    memories = await memory_svc.search_semantic(query_vector, limit=5)

    context: list[str] = []
    sources: list[dict] = []
    for item in documents:
        filename = item.get("source_file") or "Unknown document"
        page = item.get("page_number")
        page_label = f", page {page}" if page is not None else ""
        context.append(
            f"[Document: {filename}{page_label}, chunk {item.get('chunk_index', '?')}]\n{item['content']}"
        )
        citation = {
            "source_file": filename,
            "page_number": page,
            "chunk_index": item.get("chunk_index"),
        }
        if citation not in sources:
            sources.append(citation)

    if memories:
        context.append("[Relevant long-term memories]\n" + "\n".join(
            f"- {memory['content']}" for memory in memories
        ))
    return context, sources


def schedule_memory_extraction(user_message: str, conversation_id: str | None) -> None:
    task = asyncio.create_task(extract_memories(user_message, conversation_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def extract_memories(user_message: str, conversation_id: str | None) -> None:
    """Extract only stable user facts from a turn and store their embeddings."""
    try:
        prompt = (
            "Extract at most 5 durable facts explicitly stated by the user that could help "
            "future conversations (preferences, identity, ongoing work, or stable context). "
            "Ignore questions, requests, temporary details, and anything inferred. "
            "Return only a JSON array of short strings. Return [] when there are no facts.\n\n"
            f"User message: {user_message}"
        )
        raw = await ollama_svc.generate(prompt, max_tokens=256)
        start, end = raw.find("["), raw.rfind("]")
        if start < 0 or end < start:
            logger.debug("Memory extraction returned no JSON facts")
            return
        facts = json.loads(raw[start:end + 1])
        if not isinstance(facts, list):
            return
        rag = await asyncio.to_thread(get_rag)
        for fact in facts[:5]:
            if not isinstance(fact, str):
                continue
            content = fact.strip()[:1000]
            if len(content) < 8:
                continue
            vector = (await asyncio.to_thread(rag.embed_texts, [content]))[0].tolist()
            await memory_svc.add_memory(
                content=content,
                summary=content,
                importance=0.65,
                source="conversation",
                source_id=conversation_id,
                embedding=vector,
            )
    except Exception:
        logger.exception("Could not extract or save long-term memories")


async def process_and_respond(session: Session, user_message: str):
    """Stream an answer, persist the completed turn, and speak only in voice mode."""
    async with session.response_lock:
        await _process_and_respond_locked(session, user_message)


async def _process_and_respond_locked(session: Session, user_message: str):
    speech_generation = session.speech_generation
    router = get_router()

    try:
        context, sources = await retrieve_context(user_message, k=4)
        prompt = router._build_prompt(user_message, context, session.history)
        answer_parts: list[str] = []
        await session.ws.send_json({
            "type": "start",
            "conversation_id": session.conversation_id,
        })

        async for token in ollama_svc.generate_stream(prompt, model=settings.ollama_model):
            answer_parts.append(token)
            await session.ws.send_json({"type": "token", "content": token})

        answer = "".join(answer_parts).strip()
        session.history.append({"role": "user", "content": user_message})
        session.history.append({"role": "assistant", "content": answer})
        if len(session.history) > 40:
            session.history = session.history[-40:]

        if session.conversation_id:
            await conv_svc.add_message(session.conversation_id, "user", user_message)
            await conv_svc.add_message(
                session.conversation_id,
                "assistant",
                answer,
                metadata={"sources": sources},
            )
            await conv_svc.auto_title(session.conversation_id)

        await session.ws.send_json({
            "type": "done",
            "message": answer,
            "conversation_id": session.conversation_id,
            "sources": sources,
        })
        schedule_memory_extraction(user_message, session.conversation_id)

        if session.mode == "voice":
            tts = get_tts()
        else:
            tts = None
        if tts and tts.is_ready and (time.time() - session.last_audio_at) > _CANCEL_WINDOW_S:
            audio = await run_tts(tts, answer)
            if audio and speech_generation == session.speech_generation:
                await session.ws.send_bytes(audio)

    except Exception as e:
        logger.error(f"[{session.session_id}] Pipeline error: {e}")
        try:
            await session.ws.send_json({"error": str(e)})
        except Exception:
            pass


# ===================================================================
# REST Endpoints
# ===================================================================

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    ollama_ok = await ollama_svc.is_available()
    database_ok = startup_state.database == "ok"
    return JSONResponse({
        "status": "ok" if database_ok and ollama_ok else "degraded",
        "database": startup_state.database,
        "database_error": startup_state.database_error,
        "ollama": ollama_ok,
        "model": settings.ollama_model,
        "version": "0.3.0",
    })


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Small in-memory Prometheus endpoint; counters reset when the process restarts."""
    return (
        "# HELP aurora_http_requests_total Total HTTP requests handled by this process.\n"
        "# TYPE aurora_http_requests_total counter\n"
        f"aurora_http_requests_total {_request_count}\n"
        "# HELP aurora_http_server_errors_total HTTP 5xx responses and unhandled request errors.\n"
        "# TYPE aurora_http_server_errors_total counter\n"
        f"aurora_http_server_errors_total {_request_error_count}\n"
        "# HELP aurora_http_request_duration_seconds_sum Total request handling time in seconds.\n"
        "# TYPE aurora_http_request_duration_seconds_sum counter\n"
        f"aurora_http_request_duration_seconds_sum {_request_duration_seconds:.6f}\n"
    )


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
@app.get("/api/models")
async def list_models():
    models = await ollama_svc.list_models()
    if not models:
        raise OllamaUnavailableError("Cannot reach Ollama")
    return {"models": models, "active": settings.ollama_model}


@app.post("/api/models/select")
async def select_model(payload: dict):
    """Backward-compatible model selection endpoint."""
    return await set_active_model(payload)


@app.get("/api/models/active")
async def get_active_model():
    return {"active": settings.ollama_model}


async def set_active_model(payload: dict):
    model = str(payload.get("model") or "").strip()
    if not model:
        raise ValidationError("model name required")
    models = await ollama_svc.list_models()
    if not models:
        raise OllamaUnavailableError("Cannot reach Ollama or no models are installed")
    if model not in models:
        raise NotFoundError(f"Model '{model}' not found in Ollama")
    await settings_svc.set("active_model", model)
    settings.ollama_model = model
    global _router
    _router = None
    return {"active": settings.ollama_model}


@app.put("/api/models/active")
async def update_active_model(payload: dict):
    return await set_active_model(payload)


@app.get("/api/models/{model_name}/info")
async def get_model_info(model_name: str):
    info = await ollama_svc.model_info(model_name)
    if not info:
        raise NotFoundError("Model info unavailable")
    return info


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------
@app.get("/api/conversations")
async def list_conversations(limit: int = 50, offset: int = 0):
    conversations = await conv_svc.list_conversations(limit=limit, offset=offset)
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "model_name": c.model_name,
                "is_archived": c.is_archived,
            }
            for c in conversations
        ]
    }


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = await conv_svc.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        "model_name": conv.model_name,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "metadata": m.metadata_,
            }
            for m in (conv.messages or [])
        ],
    }


@app.post("/api/conversations")
async def create_conversation(payload: dict = None):
    payload = payload or {}
    conv = await conv_svc.create_conversation(
        title=payload.get("title", "New Conversation"),
        model_name=payload.get("model_name", settings.ollama_model),
    )
    return {"id": conv.id, "title": conv.title}


@app.patch("/api/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, payload: dict):
    updated = await conv_svc.update_conversation(
        conversation_id,
        title=payload.get("title"),
        is_archived=payload.get("is_archived"),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "updated"}


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    deleted = await conv_svc.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Chat (REST — for non-WebSocket clients)
# ---------------------------------------------------------------------------
@app.post("/api/chat")
async def chat_rest(payload: dict):
    """Simple REST chat endpoint for testing and API clients."""
    message = payload.get("message", "").strip()
    if not message:
        return JSONResponse({"error": "message required"}, status_code=400)

    conversation_id = payload.get("conversation_id")
    if not conversation_id:
        conv = await conv_svc.create_conversation(model_name=settings.ollama_model)
        conversation_id = conv.id

    context, sources = await retrieve_context(message, k=4)

    # History
    history = await conv_svc.get_recent_history(conversation_id, n_messages=20)

    # LLM
    router = get_router()
    answer = await run_llm(router, message, context, history)

    # Persist
    await conv_svc.add_message(conversation_id, "user", message)
    await conv_svc.add_message(
        conversation_id, "assistant", answer, metadata={"sources": sources}
    )
    await conv_svc.auto_title(conversation_id)
    schedule_memory_extraction(message, conversation_id)

    return {
        "response": answer,
        "conversation_id": conversation_id,
        "sources": sources,
    }


# ---------------------------------------------------------------------------
# Memories
# ---------------------------------------------------------------------------
@app.get("/api/memories")
async def list_memories(limit: int = 50, offset: int = 0):
    memories = await memory_svc.list_memories(limit=limit, offset=offset)
    return {
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "summary": m.summary,
                "importance": m.importance,
                "source": m.source,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "access_count": m.access_count,
            }
            for m in memories
        ]
    }


@app.post("/api/memories")
async def add_memory(payload: dict):
    content = str(payload.get("content") or "").strip()
    if not content or len(content) > 1000:
        raise ValidationError("content must be between 1 and 1000 characters")
    importance = float(payload.get("importance", 0.5))
    if not 0 <= importance <= 1:
        raise ValidationError("importance must be between 0 and 1")
    rag = await asyncio.to_thread(get_rag)
    embedding = (await asyncio.to_thread(rag.embed_texts, [content]))[0].tolist()
    mem = await memory_svc.add_memory(
        content=content,
        summary=payload.get("summary"),
        importance=importance,
        source=payload.get("source", "user"),
        embedding=embedding,
    )
    return {"id": mem.id, "content": mem.content, "importance": mem.importance}


@app.patch("/api/memories/{memory_id}")
async def update_memory(memory_id: str, payload: dict):
    content = payload.get("content")
    embedding = None
    if content is not None:
        content = str(content).strip()
        if not content or len(content) > 1000:
            raise ValidationError("content must be between 1 and 1000 characters")
        rag = await asyncio.to_thread(get_rag)
        embedding = (await asyncio.to_thread(rag.embed_texts, [content]))[0].tolist()
    importance = payload.get("importance")
    if importance is not None:
        importance = float(importance)
        if not 0 <= importance <= 1:
            raise ValidationError("importance must be between 0 and 1")
    updated = await memory_svc.update_memory(
        memory_id,
        content=content,
        summary=payload.get("summary", content),
        importance=importance,
        embedding=embedding,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found or no changes supplied")
    return {"status": "updated"}


@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    deleted = await memory_svc.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Documents (RAG management)
# ---------------------------------------------------------------------------
@app.get("/api/documents")
async def list_documents():
    docs = await doc_svc.list_documents()
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "chunk_count": d.chunk_count,
                "status": d.status,
                "error_message": d.error_message,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            }
            for d in docs
        ]
    }


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document, extract text, chunk, embed, and index."""
    from .intent.load_documents import DOCS_DIR, chunk_text, read_pages

    filename = Path((file.filename or "").replace("\\", "/")).name
    ext = Path(filename).suffix.lower()
    if ext not in {".pdf", ".txt", ".docx"}:
        return JSONResponse(
            {"error": f"Unsupported file type: {ext}. Supported: .pdf, .txt, .docx"},
            status_code=400,
        )

    max_bytes = 25 * 1024 * 1024
    content_bytes = await file.read(max_bytes + 1)
    if len(content_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the 25 MB upload limit")
    if not content_bytes:
        raise ValidationError("Uploaded file is empty")

    storage_key = f"{uuid.uuid4().hex}{ext}"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DOCS_DIR / storage_key
    doc = await doc_svc.add_document(
        filename=filename,
        file_type=ext.lstrip("."),
        file_size=len(content_bytes),
        chunk_count=0,
        status="processing",
        storage_key=storage_key,
    )

    try:
        await asyncio.to_thread(file_path.write_bytes, content_bytes)
        pages = await asyncio.to_thread(read_pages, file_path)
        if not any(text.strip() for text, _ in pages):
            raise ValueError("No text could be extracted from the document")
        chunks = []
        chunk_index = 0
        for page_text, page_number in pages:
            for content in chunk_text(page_text):
                chunks.append({
                    "source_file": filename,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "content": content,
                })
                chunk_index += 1
        if not chunks:
            raise ValueError("No readable text chunks were found")

        rag = await asyncio.to_thread(get_rag)
        vectors = await asyncio.to_thread(
            rag.embed_texts, [chunk["content"] for chunk in chunks]
        )
        for chunk, vector in zip(chunks, vectors):
            chunk["embedding"] = vector.tolist()

        await doc_svc.replace_chunks(doc.id, chunks)
        await doc_svc.update_document(
            doc.id, status="indexed", chunk_count=len(chunks), error_message=""
        )
        all_chunks = await doc_svc.list_chunks()
        await asyncio.to_thread(rag.build, all_chunks)
        return {
            "id": doc.id,
            "filename": doc.filename,
            "chunks": len(chunks),
            "pages": sum(1 for _, page in pages if page is not None),
            "status": "indexed",
        }

    except Exception as e:
        logger.exception("Document processing failed: %s", filename)
        file_path.unlink(missing_ok=True)
        await doc_svc.update_document(
            doc.id,
            status="failed",
            error_message=str(e)[:1000],
        )
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    doc = await doc_svc.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await doc_svc.delete_document(document_id)
    from .intent.load_documents import DOCS_DIR
    storage_key = Path(doc.storage_key or doc.filename).name
    file_path = DOCS_DIR / storage_key
    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        logger.exception("Could not remove uploaded file %s", storage_key)
    rag = await asyncio.to_thread(get_rag)
    all_chunks = await doc_svc.list_chunks()
    await asyncio.to_thread(rag.build, all_chunks)
    return {"status": "deleted"}


@app.post("/index")
async def rebuild_index():
    """Re-build the FAISS vector store from documents in backend/data/docs/."""
    from .intent.load_documents import load_all_chunks
    rag = await asyncio.to_thread(get_rag)
    chunks = await doc_svc.list_chunks()
    if not chunks:
        chunks = await asyncio.to_thread(load_all_chunks)
    await asyncio.to_thread(rag.build, chunks)
    return {"chunks": len(chunks)}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
@app.get("/api/settings")
async def get_settings():
    all_settings = await settings_svc.get_all()
    all_settings.pop("voice_auth_profile", None)
    all_settings.setdefault("speech_rate", _speech_rate)
    return {"settings": all_settings}


@app.post("/api/settings")
async def update_settings(payload: dict):
    global _speech_rate
    if "voice_auth_profile" in payload:
        raise ValidationError("Voice profiles must be changed through the voice-auth endpoints")
    if "speech_rate" in payload:
        try:
            requested_rate = int(payload["speech_rate"])
        except (TypeError, ValueError) as exc:
            raise ValidationError("speech_rate must be an integer from 100 to 300") from exc
        if not 100 <= requested_rate <= 300:
            raise ValidationError("speech_rate must be between 100 and 300")
        payload["speech_rate"] = requested_rate
        _speech_rate = requested_rate
        if _tts:
            _tts.set_rate(requested_rate)
    for key, value in payload.items():
        await settings_svc.set(key, value)
    return {"status": "updated"}


# ---------------------------------------------------------------------------
# Agent tools and task planning
# ---------------------------------------------------------------------------
@app.get("/api/agent/tools")
async def list_agent_tools():
    return {"tools": TOOL_SCHEMAS}


@app.post("/api/agent/plan")
async def plan_agent_task(payload: dict):
    task = str(payload.get("task", "")).strip()
    if not 2 <= len(task) <= 1000:
        raise ValidationError("task must contain between 2 and 1000 characters")
    schema = json.dumps(TOOL_SCHEMAS, ensure_ascii=False)
    prompt = (
        "Create a short plan for a local desktop assistant. Choose only tools from the tool list. "
        "Never invent a tool, shell command, executable, path, or argument. A user must approve "
        "the plan before it runs. Return only JSON in this shape: "
        '{"steps":[{"tool":"tool_name","arguments":{},"reason":"short explanation"}]}. '
        "Use at most 5 steps. If the task is unsupported, return {\"steps\":[]} .\n"
        f"Tools: {schema}\nTask: {task}"
    )
    raw = await ollama_svc.generate(prompt, temperature=0, max_tokens=512)
    try:
        decoded = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        raw_steps = decoded.get("steps", [])
        if not isinstance(raw_steps, list) or len(raw_steps) > 5:
            raise ValueError("Plan must contain at most five steps")
        steps = []
        for item in raw_steps:
            name = item.get("tool")
            args = validate_arguments(name, item.get("arguments", {}))
            steps.append({
                "tool": name,
                "arguments": args,
                "reason": str(item.get("reason", "Run the selected local tool."))[:300],
                "confirmation_required": True,
                "sensitive": name in SENSITIVE_TOOLS,
            })
        if not steps:
            raise ValidationError("Aurora could not create a plan using the available local tools.")
    except ValidationError:
        raise
    except Exception as exc:
        logger.info("Agent returned an unusable plan: %s", exc)
        raise ValidationError("Aurora could not create a valid tool plan. Try a more specific task.") from exc
    run = await agent_svc.create(task, steps)
    return {"plan_id": run.id, "task": task, "steps": steps, "status": run.status}


@app.post("/api/agent/execute")
async def execute_agent_plan(payload: dict):
    run_id = str(payload.get("plan_id", ""))
    if payload.get("confirmed") is not True:
        raise ValidationError("Review the plan and explicitly confirm before execution.")
    async with _agent_execution_lock:
        run = await agent_svc.get(run_id)
        if not run:
            raise NotFoundError("Agent plan was not found.")
        if run.status != "awaiting_confirmation":
            raise ValidationError("This plan has already been executed or cancelled.")
        await agent_svc.update(run_id, "running")
        results = []
        failed = False
        for step in run.plan:
            try:
                output = await asyncio.to_thread(execute_tool, step["tool"], step["arguments"])
                results.append({"tool": step["tool"], "ok": True, "output": output})
            except Exception as exc:
                failed = True
                results.append({"tool": step["tool"], "ok": False, "error": str(exc)[:500]})
                break

        # Inject observed tool results into a final response; this model cannot initiate extra tools.
        summary_prompt = (
            "Summarize the completed local tool results for the user's request. Report failures clearly. "
            "Do not claim actions that are absent from the results and do not request or execute more tools.\n"
            f"User task: {run.task}\nTool results: {json.dumps(results, ensure_ascii=False)}"
        )
        summary = await ollama_svc.generate(summary_prompt, temperature=0.2, max_tokens=300)
        persisted = []
        for item in results:
            saved = dict(item)
            if item["tool"] == "clipboard_read" and item.get("ok"):
                saved["output"] = {"text": "[clipboard content omitted from execution history]"}
            persisted.append(saved)
        await agent_svc.update(run_id, "partial" if failed else "completed", {"steps": persisted, "summary": summary})
        return {
            "plan_id": run_id,
            "status": "partial" if failed else "completed",
            "results": results,
            "summary": summary,
        }


@app.post("/api/agent/{plan_id}/cancel")
async def cancel_agent_plan(plan_id: str):
    async with _agent_execution_lock:
        run = await agent_svc.get(plan_id)
        if not run:
            raise NotFoundError("Agent plan was not found.")
        if run.status != "awaiting_confirmation":
            raise ValidationError("Only plans awaiting confirmation can be cancelled.")
        await agent_svc.update(plan_id, "cancelled", None)
        return {"status": "cancelled"}


@app.get("/api/agent/history")
async def agent_history():
    runs = await agent_svc.list()
    return {"runs": [{
        "id": run.id, "task": run.task, "plan": run.plan, "status": run.status,
        "result": run.result, "created_at": run.created_at.isoformat(),
    } for run in runs]}


# ---------------------------------------------------------------------------
# Opt-in convenience voice profile (not a security authenticator)
# ---------------------------------------------------------------------------
@app.get("/api/voice-auth/status")
async def voice_auth_status():
    profile = await settings_svc.get("voice_auth_profile")
    return {
        "enrolled": bool(profile),
        "warning": "Voice matching is approximate and must not be used as a security control.",
    }


@app.post("/api/voice-auth/enroll")
async def enroll_voice(request: Request):
    audio = await request.body()
    if len(audio) > 5_000_000:
        raise ValidationError("Voice sample exceeds the 5 MB limit")
    try:
        embedding = await asyncio.to_thread(voice_embedding, audio)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    await settings_svc.set("voice_auth_profile", {"embedding": embedding, "created_at": time.time()})
    return {
        "enrolled": True,
        "message": "Voice profile saved locally. This approximate match is not security-grade authentication.",
    }


@app.post("/api/voice-auth/verify")
async def verify_voice(request: Request):
    profile = await settings_svc.get("voice_auth_profile")
    if not profile or not profile.get("embedding"):
        raise ValidationError("Enroll a voice profile before verification")
    audio = await request.body()
    if len(audio) > 5_000_000:
        raise ValidationError("Voice sample exceeds the 5 MB limit")
    try:
        sample = await asyncio.to_thread(voice_embedding, audio)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    score = similarity(profile["embedding"], sample)
    threshold = 0.82
    return {
        "matched": score >= threshold,
        "score": round(score, 3),
        "threshold": threshold,
        "warning": "Approximate local speaker match only; not suitable for protecting actions or data.",
    }


@app.delete("/api/voice-auth/profile")
async def delete_voice_profile():
    deleted = await settings_svc.delete("voice_auth_profile")
    return {"deleted": deleted}


# ===================================================================
# WebSocket Endpoints
# ===================================================================

# ---------------------------------------------------------------------------
# WebSocket: Chat
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    # Allow optional conversation_id query param to resume
    conversation_id = websocket.query_params.get("conversation_id")
    mode = websocket.query_params.get("mode", "voice")
    if mode not in {"chat", "voice"}:
        await websocket.close(code=1008, reason="mode must be chat or voice")
        return
    session = await sessions.connect(websocket, conversation_id, mode)
    logger.info(f"Chat WS connected: {session.session_id} (conv: {session.conversation_id})")
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "connected",
            "session_id": session.session_id,
            "conversation_id": session.conversation_id,
        })
        if mode == "voice":
            greeting = f"Welcome back, {settings.user_name}! How can I help you today?"
            await websocket.send_json({"type": "message", "message": greeting})
            tts = get_tts()
            if tts.is_ready:
                audio = await run_tts(tts, greeting)
                if audio:
                    await websocket.send_bytes(audio)

        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                if payload.get("type") == "interrupt":
                    session.speech_generation += 1
                    session.last_audio_at = time.time()
                    continue
                user_message = payload.get("message") or raw
            except Exception:
                user_message = raw

            if not user_message.strip():
                continue

            task = asyncio.create_task(process_and_respond(session, user_message))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

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
    try:
        # Keep segmentation state isolated per audio connection.
        vad = VoiceActivityDetector()
    except RuntimeError as exc:
        await websocket.send_json({"error": str(exc)})
        await websocket.close(code=1011)
        return

    logger.info(f"Audio WS connected for session: {session_id}")
    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"]:
                audio_buffer.extend(msg["bytes"])
                while len(audio_buffer) >= BYTES_PER_FRAME:
                    frame = bytes(audio_buffer[:BYTES_PER_FRAME])
                    del audio_buffer[:BYTES_PER_FRAME]
                    segment = vad.process_frame(frame)
                    if segment:
                        session.last_audio_at = time.time()
                        if not stt.is_ready:
                            await websocket.send_json({
                                "error": (
                                    "Speech recognition model is not ready. "
                                    "Install backend requirements and restart Aurora."
                                )
                            })
                            continue
                        transcript = await asyncio.to_thread(stt.transcribe_pcm, segment)
                        await websocket.send_json({"transcript": transcript or ""})
                        if transcript:
                            session.speech_generation += 1
                            task = asyncio.create_task(process_and_respond(session, transcript))
                            _background_tasks.add(task)
                            task.add_done_callback(_background_tasks.discard)
            elif "text" in msg and msg["text"]:
                try:
                    command = json.loads(msg["text"])
                except json.JSONDecodeError:
                    continue
                if command.get("type") == "flush":
                    segment = vad.flush()
                    if segment and stt.is_ready:
                        session.last_audio_at = time.time()
                        transcript = await asyncio.to_thread(stt.transcribe_pcm, segment)
                        await websocket.send_json({"transcript": transcript or ""})
                        if transcript:
                            session.speech_generation += 1
                            task = asyncio.create_task(process_and_respond(session, transcript))
                            _background_tasks.add(task)
                            task.add_done_callback(_background_tasks.discard)

    except WebSocketDisconnect:
        logger.info(f"Audio WS disconnected: {session_id}")
        vad.flush()
    except Exception as e:
        logger.error(f"Audio WS error: {e}")


# Serve the production React bundle when packaged or when a local build exists.
_source_root = Path(__file__).resolve().parents[2]
_bundle_root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else None
_frontend_dist = find_frontend_dist(_source_root, _bundle_root)
if _frontend_dist:
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    async def root_status():
        return {"name": "Aurora Assistant API", "status": "ok"}
