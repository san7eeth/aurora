"""The existing WebSocket integration suite verifies connect, stream events and disconnect."""
import pytest

from app.services.ollama_service import OllamaService


@pytest.mark.asyncio
async def test_stream_parser_keeps_each_nonempty_chunk(monkeypatch):
    import httpx

    lines = b'{"response":"one"}\n\n{"response":"two"}\n{"response":""}\n{"done":true}\n'
    client_type = httpx.AsyncClient
    monkeypatch.setattr(
        "app.services.ollama_service.httpx.AsyncClient",
        lambda **kwargs: client_type(
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(200, content=lines)
            ),
            **kwargs,
        ),
    )
    result = [chunk async for chunk in OllamaService("http://ollama.test").generate_stream("prompt")]
    assert result == ["one", "two"]
