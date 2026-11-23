"""Unit tests — core config, errors, logging, and startup checks."""
import json
import logging

import pytest

from app.core.config import resolve_sqlite_url
from app.core.exceptions import (
    AuroraError,
    ConfigurationError,
    NotFoundError,
    OllamaUnavailableError,
    ValidationError,
)
from app.core.logging_config import JSONFormatter


def test_validation_error_status():
    err = ValidationError("model name required")
    assert isinstance(err, AuroraError)
    assert err.status_code == 400
    assert err.message == "model name required"


def test_not_found_and_ollama_status_codes():
    assert NotFoundError("missing").status_code == 404
    assert OllamaUnavailableError().status_code == 503


def test_relative_sqlite_url_resolves_under_backend_data():
    url, path = resolve_sqlite_url("sqlite+aiosqlite:///./aurora.db")
    assert path.name == "aurora.db"
    assert path.parent.name == "data"
    assert url == f"sqlite+aiosqlite:///{path.as_posix()}"


def test_unsupported_database_url_raises():
    with pytest.raises(ConfigurationError):
        resolve_sqlite_url("postgresql://localhost/aurora")


def test_json_formatter_emits_single_line_json():
    record = logging.LogRecord(
        name="aurora.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=None,
        exc_info=None,
    )
    payload = json.loads(JSONFormatter().format(record))
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "aurora.test"


@pytest.mark.asyncio
async def test_startup_checks_record_database_and_ollama(monkeypatch):
    import app.core.health as health

    class FakeConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, _statement):
            return None

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    class FakeOllamaService:
        async def is_available(self):
            return True

        async def list_models(self):
            return ["llama3.2:3b"]

    init_db_calls = 0

    async def fake_init_db():
        nonlocal init_db_calls
        init_db_calls += 1

    monkeypatch.setattr(health, "engine", FakeEngine())
    monkeypatch.setattr(health, "init_db", fake_init_db)

    state = await health.run_startup_checks(FakeOllamaService())

    assert init_db_calls == 1
    assert state.database == "ok"
    assert state.database_error is None
    assert state.ollama is True
    assert state.models == ["llama3.2:3b"]
