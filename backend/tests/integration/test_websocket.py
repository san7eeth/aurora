"""Integration tests — WebSocket /ws and /ws/audio endpoints."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_ws_chat_connect_returns_session_id():
    """On connect, client must receive connected message with UUID session_id."""
    with patch("app.intent.intent_router.IntentRouter.generate", return_value="hi"), \
         patch("app.perception.tts.Pyttsx3TTS.synthesize", return_value=None), \
         patch("app.intent.rag_service.RAGService.retrieve", return_value=[]):
        from app.api import app
        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            msg = ws.receive_json()
            assert msg["message"] == "connected"
            assert "session_id" in msg
            sid = msg["session_id"]
            assert len(sid) == 36  # UUID format: 8-4-4-4-12


@pytest.mark.integration
def test_ws_chat_receives_greeting():
    """After session_id, server sends personalised greeting."""
    with patch("app.intent.intent_router.IntentRouter.generate", return_value="hi"), \
         patch("app.perception.tts.Pyttsx3TTS.synthesize", return_value=None), \
         patch("app.intent.rag_service.RAGService.retrieve", return_value=[]):
        from app.api import app
        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # connected
            greeting = ws.receive_json()
            assert "message" in greeting
            assert len(greeting["message"]) > 5


@pytest.mark.integration
def test_ws_chat_send_and_receive():
    """Client sends message; server responds with LLM answer."""
    with patch("app.intent.intent_router.IntentRouter.generate",
               return_value="Aurora responding!"), \
         patch("app.perception.tts.Pyttsx3TTS.synthesize", return_value=None), \
         patch("app.intent.rag_service.RAGService.retrieve", return_value=[]):
        from app.api import app
        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # connected
            ws.receive_json()  # greeting
            ws.send_json({"message": "Hello Aurora!"})
            response = ws.receive_json()
            assert "message" in response
            assert response["message"] == "Aurora responding!"


@pytest.mark.integration
def test_ws_audio_missing_session_id_returns_error():
    """Audio WS without session_id query param must send error and close."""
    from app.api import app
    client = TestClient(app)
    with client.websocket_connect("/ws/audio") as ws:
        err = ws.receive_json()
        assert "error" in err


@pytest.mark.integration
def test_ws_audio_invalid_session_id_returns_error():
    """Audio WS with non-existent session_id must return error."""
    from app.api import app
    client = TestClient(app)
    with client.websocket_connect("/ws/audio?session_id=does-not-exist") as ws:
        err = ws.receive_json()
        assert "error" in err
