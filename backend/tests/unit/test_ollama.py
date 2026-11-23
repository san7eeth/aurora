"""Ollama HTTP behavior is tested with an in-process HTTPX transport."""
import httpx
import pytest

from app.services.ollama_service import OllamaService


def _client_factory(monkeypatch, handler):
    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        "app.services.ollama_service.httpx.AsyncClient",
        lambda **kwargs: original_client(transport=transport, **kwargs),
    )


@pytest.mark.asyncio
async def test_ollama_availability_and_model_listing(monkeypatch):
    def handler(request):
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "alpha:latest"}, {"name": "beta:small"}]})

    _client_factory(monkeypatch, handler)
    service = OllamaService("http://ollama.test")
    assert await service.is_available() is True
    assert await service.list_models() == ["alpha:latest", "beta:small"]


@pytest.mark.asyncio
async def test_ollama_unavailable_and_model_list_fail_closed(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("offline", request=request)

    _client_factory(monkeypatch, handler)
    service = OllamaService("http://ollama.test")
    assert await service.is_available() is False
    assert await service.list_models() == []


@pytest.mark.asyncio
async def test_ollama_stream_yields_incremental_response_tokens(monkeypatch):
    def stream_handler(request):
        assert request.url.path == "/api/generate"
        assert request.read()
        return httpx.Response(200, content=b'{"response":"first "}\n{"response":"second"}\n{"done":true}\n')

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.services.ollama_service.httpx.AsyncClient",
        lambda **kwargs: original_client(transport=httpx.MockTransport(stream_handler), **kwargs),
    )
    service = OllamaService("http://ollama.test")
    assert [token async for token in service.generate_stream("hello", model="alpha")] == ["first ", "second"]
