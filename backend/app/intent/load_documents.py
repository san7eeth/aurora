"""Read supported local documents and split their text into retrieval chunks."""

from pathlib import Path
from typing import List
import os
import re
from pypdf import PdfReader
from docx import Document
from ..core.config import APP_DATA_DIR


DOCS_DIR = Path(
    os.environ.get("AURORA_DOCUMENTS_DIR", APP_DATA_DIR / "docs")
).expanduser().resolve()


def list_supported_documents() -> List[Path]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    exts = {".pdf", ".txt", ".docx"}
    return [p for p in DOCS_DIR.glob("**/*") if p.suffix.lower() in exts]


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if path.suffix.lower() == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


def read_pages(path: Path) -> list[tuple[str, int | None]]:
    """Read document text while preserving PDF page numbers when available."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return [
            (page.extract_text() or "", page_number)
            for page_number, page in enumerate(reader.pages, start=1)
        ]
    if suffix == ".txt":
        return [(path.read_text(encoding="utf-8", errors="ignore"), None)]
    if suffix == ".docx":
        doc = Document(str(path))
        content = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return [(content, None)]
    return []


def chunk_text(text: str, max_tokens: int = 400) -> List[str]:
    # naive chunking by sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for s in sentences:
        sl = len(s.split())
        if current_len + sl > max_tokens and current:
            chunks.append(" ".join(current))
            current = [s]
            current_len = sl
        else:
            current.append(s)
            current_len += sl
    if current:
        chunks.append(" ".join(current))
    return [c.strip() for c in chunks if c.strip()]


def load_all_chunks() -> List[str]:
    files = list_supported_documents()
    all_chunks: List[str] = []
    for f in files:
        txt = read_text(f)
        all_chunks.extend(chunk_text(txt))
    return all_chunks
