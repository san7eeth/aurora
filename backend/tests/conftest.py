"""
Shared pytest fixtures for Aurora test suite.
All external services (Ollama, TTS, STT, RAG) are mocked by default.
"""
import pytest
from unittest.mock import patch, AsyncMock


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
        yield mock_svc


@pytest.fixture
def test_client(mock_intent_router, mock_rag_service, mock_tts, mock_stt, mock_ollama_service):
    """FastAPI TestClient with all external services mocked."""
    from fastapi.testclient import TestClient
    from app.api import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
