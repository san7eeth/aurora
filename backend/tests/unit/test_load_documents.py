"""Unit tests — document loading and chunking."""
import os
import tempfile
from pathlib import Path
from app.intent.load_documents import chunk_text, read_text


def test_chunk_text_returns_list():
    chunks = chunk_text("Hello world. This is sentence two. And three.")
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_chunk_text_all_strings():
    chunks = chunk_text("One sentence. Two sentences. Three sentences.")
    assert all(isinstance(c, str) for c in chunks)


def test_chunk_text_empty_input():
    assert chunk_text("") == []


def test_chunk_text_respects_max_tokens():
    long_text = ("word " * 50 + ". ") * 10
    chunks = chunk_text(long_text, max_tokens=60)
    for chunk in chunks:
        word_count = len(chunk.split())
        assert word_count <= 150, f"Chunk too long: {word_count} words"


def test_read_text_txt_file():
    with tempfile.NamedTemporaryFile(
        suffix=".txt", mode="w", delete=False, encoding="utf-8"
    ) as f:
        f.write("Hello from Aurora test.")
        tmp = f.name
    try:
        result = read_text(Path(tmp))
        assert "Hello from Aurora test." in result
    finally:
        os.unlink(tmp)


def test_read_text_unknown_extension_returns_empty():
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"binary data")
        tmp = f.name
    try:
        result = read_text(Path(tmp))
        assert result == ""
    finally:
        os.unlink(tmp)
