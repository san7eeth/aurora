"""Unit tests — RAGService."""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.intent.rag_service import RAGService


@pytest.fixture
def rag(tmp_path):
    """RAGService with mocked embedder and temp storage dirs."""
    with patch("app.intent.rag_service.SentenceTransformer") as MockST, \
         patch("app.intent.rag_service.STORE_DIR", tmp_path):
        mock_model = MagicMock()
        MockST.return_value = mock_model
        service = RAGService()
        yield service, mock_model


def test_retrieve_empty_when_no_index(rag):
    service, _ = rag
    assert service.retrieve("anything") == []


def test_build_creates_index(rag):
    service, mock_model = rag
    chunks = ["alpha", "beta", "gamma"]
    mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)
    service.build(chunks)
    assert service._index is not None
    assert service._texts == chunks


def test_build_empty_clears_state(rag):
    service, mock_model = rag
    mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
    service.build(["a", "b"])
    service.build([])
    assert service._index is None
    assert service._texts == []


def test_retrieve_after_build(rag):
    service, mock_model = rag
    chunks = ["Python is a programming language.", "FastAPI is an async framework."]
    build_emb = np.random.rand(2, 384).astype(np.float32)
    query_emb = np.random.rand(1, 384).astype(np.float32)
    mock_model.encode.side_effect = [build_emb, query_emb]
    service.build(chunks)
    results = service.retrieve("Python framework", k=2)
    assert isinstance(results, list)
    assert len(results) <= 2
    for text, score in results:
        assert isinstance(text, str)
        assert isinstance(score, float)


def test_retrieve_k_respects_limit(rag):
    service, mock_model = rag
    chunks = ["one", "two", "three", "four", "five"]
    build_emb = np.random.rand(5, 384).astype(np.float32)
    query_emb = np.random.rand(1, 384).astype(np.float32)
    mock_model.encode.side_effect = [build_emb, query_emb]
    service.build(chunks)
    results = service.retrieve("test", k=2)
    assert len(results) <= 2
