"""Startup probes are isolated from external Ollama and the developer database."""
import pytest

from app.core import health


class FakeConnection:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def execute(self, _statement):
        return 1


class FakeEngine:
    def connect(self):
        return FakeConnection()


@pytest.mark.asyncio
async def test_startup_marks_database_and_ollama_ready(monkeypatch):
    async def initialized():
        return None

    class Ollama:
        async def is_available(self):
            return True

        async def list_models(self):
            return ["test-model"]

    monkeypatch.setattr(health, "init_db", initialized)
    monkeypatch.setattr(health, "engine", FakeEngine())
    monkeypatch.setattr(health.startup_state, "database", "pending")
    monkeypatch.setattr(health.startup_state, "database_error", None)
    monkeypatch.setattr(health.startup_state, "ollama", False)
    monkeypatch.setattr(health.startup_state, "models", [])
    state = await health.run_startup_checks(Ollama())
    assert state.database == "ok"
    assert state.database_error is None
    assert state.ollama is True
    assert state.models == ["test-model"]


@pytest.mark.asyncio
async def test_startup_reports_database_failure_and_ollama_degraded(monkeypatch):
    async def fail_init():
        raise RuntimeError("database unavailable")

    class Ollama:
        async def is_available(self):
            return False

        async def list_models(self):
            raise AssertionError("must not list models when unavailable")

    monkeypatch.setattr(health, "init_db", fail_init)
    monkeypatch.setattr(health.startup_state, "database", "pending")
    monkeypatch.setattr(health.startup_state, "database_error", None)
    monkeypatch.setattr(health.startup_state, "ollama", False)
    monkeypatch.setattr(health.startup_state, "models", [])
    state = await health.run_startup_checks(Ollama())
    assert state.database == "error"
    assert "database unavailable" in (state.database_error or "")
    assert state.ollama is False
    assert state.models == []
