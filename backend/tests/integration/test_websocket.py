"""WebSocket integration checks with local model and retrieval services isolated."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class LocalOllamaStub:
    async def is_available(self):
        return True

    async def list_models(self):
        return ["test-model"]

    async def generate(self, *_args, **_kwargs):
        return "[]"

    async def generate_stream(self, *_args, **_kwargs):
        yield "Aurora "
        yield "responding!"


@pytest.fixture
def websocket_client(isolated_database, monkeypatch):
    from app.api import app
    from app.core.health import startup_state
    from app.config import settings

    monkeypatch.setattr(settings, "ollama_model", "llama3.2:3b")
    startup_state.database = "pending"
    startup_state.database_error = None

    with patch("app.api.ollama_svc", LocalOllamaStub()), \
            patch("app.api.retrieve_context", new=AsyncMock(return_value=([], []))), \
            patch("app.api.get_tts", return_value=SimpleNamespace(is_ready=False)):
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client


@pytest.mark.integration
def test_ws_chat_connect_returns_session_id(websocket_client):
    with websocket_client.websocket_connect("/ws?mode=chat") as ws:
        connected = ws.receive_json()
        assert connected["type"] == "connected"
        assert len(connected["session_id"]) == 36


@pytest.mark.integration
def test_voice_session_sends_greeting(websocket_client):
    with websocket_client.websocket_connect("/ws?mode=voice") as ws:
        assert ws.receive_json()["type"] == "connected"
        greeting = ws.receive_json()
        assert greeting["type"] == "message"
        assert "How can I help" in greeting["message"]


@pytest.mark.integration
def test_ws_chat_streams_response_events(websocket_client):
    with websocket_client.websocket_connect("/ws?mode=chat") as ws:
        ws.receive_json()
        ws.send_json({"message": "Hello Aurora"})
        events = [ws.receive_json() for _ in range(4)]
        assert [event["type"] for event in events] == ["start", "token", "token", "done"]
        assert events[-1]["message"] == "Aurora responding!"


@pytest.mark.integration
def test_ws_audio_missing_session_id_returns_error(websocket_client):
    with websocket_client.websocket_connect("/ws/audio") as ws:
        assert "error" in ws.receive_json()


@pytest.mark.integration
def test_ws_audio_invalid_session_id_returns_error(websocket_client):
    with websocket_client.websocket_connect("/ws/audio?session_id=does-not-exist") as ws:
        assert "error" in ws.receive_json()
