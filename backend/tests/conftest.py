"""
Shared pytest fixtures for Aurora test suite.
All external services (Ollama, TTS, STT, RAG) are mocked by default.
"""
import pytest
from unittest.mock import patch, AsyncMock
import asyncio
import importlib


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Give each API test a disposable SQLite database, never the user's app DB."""
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.database.models import Base
    from app.core.health import startup_state

    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'aurora-test.db'}",
        poolclass=NullPool,
    )
    test_sessions = async_sessionmaker(test_engine, expire_on_commit=False)
    for module_name in (
        "app.services.conversation_service",
        "app.services.memory_service",
        "app.services.document_service",
        "app.services.settings_service",
        "app.services.agent_service",
    ):
        module = importlib.import_module(module_name)
        monkeypatch.setattr(module, "async_session", test_sessions)

    health = importlib.import_module("app.core.health")
    monkeypatch.setattr(health, "engine", test_engine)

    async def create_test_schema():
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(health, "init_db", create_test_schema)
    prior_state = (
        startup_state.database,
        startup_state.database_error,
        startup_state.ollama,
        list(startup_state.models),
    )
    startup_state.database = "pending"
    startup_state.database_error = None
    startup_state.ollama = False
    startup_state.models = []
    yield test_engine
    startup_state.database, startup_state.database_error, startup_state.ollama, startup_state.models = prior_state
    asyncio.run(test_engine.dispose())


@pytest.fixture
def mock_intent_router():
    """Mocked IntentRouter — never calls Ollama."""
    with patch("app.intent.intent_router.IntentRouter.generate") as mock_gen:
        mock_gen.return_value = "Mock LLM response for testing."
        yield mock_gen


@pytest.fixture
def mock_rag_service():
    """Mocked RAGService — returns empty results."""
    with patch("app.intent.rag_service.RAGService.retrieve") as mock_ret:
        mock_ret.return_value = []
        yield mock_ret


@pytest.fixture
def mock_tts():
    """Mocked TTS — returns None (no audio bytes)."""
    with patch("app.perception.tts.Pyttsx3TTS.synthesize") as mock_synth:
        mock_synth.return_value = None
        yield mock_synth


@pytest.fixture
def mock_stt():
    """Mocked STT — returns preset transcript."""
    with patch("app.perception.stt.WhisperSTT.transcribe_chunk") as mock_trans:
        mock_trans.return_value = "Hello Aurora"
        yield mock_trans


@pytest.fixture
def mock_ollama_service():
    """Mock OllamaService methods used in the API layer."""
    with patch("app.api.ollama_svc") as mock_svc:
        mock_svc.is_available = AsyncMock(return_value=True)
        mock_svc.list_models = AsyncMock(return_value=["llama3.2:3b", "phi3:mini"])
        mock_svc.model_info = AsyncMock(return_value={"name": "llama3.2:3b"})
        mock_svc.generate = AsyncMock(return_value="[]")

        async def generate_stream(*_args, **_kwargs):
            yield "Mock "
            yield "streamed response."
        mock_svc.generate_stream = generate_stream
        yield mock_svc


@pytest.fixture
def test_client(mock_intent_router, mock_tts, mock_stt, mock_ollama_service, isolated_database, monkeypatch):
    """FastAPI TestClient with all external services mocked."""
    from fastapi.testclient import TestClient
    from app.api import app
    from app.config import settings
    monkeypatch.setattr(settings, "ollama_model", "llama3.2:3b")
    with patch("app.api.retrieve_context", new=AsyncMock(return_value=([], []))):
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
