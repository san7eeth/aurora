"""Unit tests — IntentRouter."""
import pytest
from unittest.mock import patch
from app.intent.intent_router import IntentRouter, SYSTEM_PROMPT


def test_system_prompt_mentions_aurora():
    assert "Aurora" in SYSTEM_PROMPT


def test_system_prompt_mentions_privacy():
    assert "privacy" in SYSTEM_PROMPT.lower() or "local" in SYSTEM_PROMPT.lower()


def test_build_prompt_includes_user_message():
    router = IntentRouter()
    prompt = router._build_prompt("What is 2+2?", [], [])
    assert "What is 2+2?" in prompt


def test_build_prompt_includes_context_chunks():
    router = IntentRouter()
    prompt = router._build_prompt("test", ["important fact"], [])
    assert "important fact" in prompt


def test_build_prompt_includes_history():
    router = IntentRouter()
    history = [
        {"role": "user", "content": "Who are you?"},
        {"role": "assistant", "content": "I am Aurora."},
    ]
    prompt = router._build_prompt("Tell me more", [], history)
    assert "Who are you?" in prompt
    assert "I am Aurora." in prompt


def test_history_truncated_to_last_10():
    router = IntentRouter()
    history = [{"role": "user", "content": f"message_{i}"} for i in range(20)]
    prompt = router._build_prompt("new question", [], history)
    assert "message_19" in prompt
    assert "message_0" not in prompt


def test_route_uses_mocked_generate(mock_intent_router):
    router = IntentRouter()
    result = router.route("Hello", [], [])
    assert result == "Mock LLM response for testing."
    mock_intent_router.assert_called_once()


def test_generate_handles_connection_error():
    """Should return user-friendly message when Ollama is unreachable."""
    router = IntentRouter(ollama_base="http://127.0.0.1:1")
    result = router.generate("test prompt")
    assert any(w in result.lower() for w in ["unable", "connect", "error", "failed", "unavailable"])


def test_route_with_empty_history():
    with patch.object(IntentRouter, "generate", return_value="ok"):
        router = IntentRouter()
        result = router.route("hi", [], None)
    assert result == "ok"
