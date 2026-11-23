"""Unit tests — config module."""
from app.config import settings


def test_ollama_url_is_http():
    assert settings.ollama_base_url.startswith("http")


def test_model_name_not_empty():
    assert len(settings.ollama_model) > 0


def test_port_is_valid_integer():
    assert isinstance(settings.backend_port, int)
    assert 1 <= settings.backend_port <= 65535


def test_user_name_not_empty():
    assert len(settings.user_name) > 0


def test_log_level_is_valid():
    valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    assert settings.log_level.upper() in valid
