"""Malformed local inputs and unreachable services fail safely."""
import httpx
import pytest

from app.intent.load_documents import read_text
from app.services.ollama_service import OllamaService


def test_corrupt_pdf_is_reported_as_a_parse_error(tmp_path):
    corrupt = tmp_path / "broken.pdf"
    corrupt.write_bytes(b"not a PDF file")
    with pytest.raises(Exception):
        read_text(corrupt)


def test_unsupported_document_extension_returns_empty_text(tmp_path):
    unknown = tmp_path / "ignored.bin"
    unknown.write_bytes(b"data")
    assert read_text(unknown) == ""


@pytest.mark.asyncio
async def test_generation_connection_failure_returns_helpful_message(monkeypatch):
    original_client = httpx.AsyncClient

    def handler(request):
        raise httpx.ConnectError("offline", request=request)

    monkeypatch.setattr(
        "app.services.ollama_service.httpx.AsyncClient",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    answer = await OllamaService("http://ollama.test").generate("hello")
    assert "unable to connect" in answer.lower()
