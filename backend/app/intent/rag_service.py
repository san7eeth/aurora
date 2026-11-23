"""
FAISS vector store + sentence-transformers embeddings + simple retrieval.
"""

from typing import List, Tuple
from pathlib import Path
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STORE_DIR = DATA_DIR / "vectorstore"
STORE_DIR.mkdir(parents=True, exist_ok=True)


class RAGService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(model_name)
        self.index_path = STORE_DIR / "faiss.index"
        self.texts_path = STORE_DIR / "texts.npy"
        self.metadata_path = STORE_DIR / "metadata.json"
        self._index: faiss.IndexFlatIP | None = None
        self._texts: List[str] = []
        self._metadata: list[dict] = []
        self._load()

    def _load(self):
        if self.index_path.exists() and self.texts_path.exists():
            self._index = faiss.read_index(str(self.index_path))
            self._texts = np.load(self.texts_path, allow_pickle=True).tolist()
            if self.metadata_path.exists():
                self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            else:
                self._metadata = [{"source_file": None, "page_number": None, "chunk_index": i} for i in range(len(self._texts))]

    def _save(self):
        if self._index is not None:
            faiss.write_index(self._index, str(self.index_path))
        np.save(self.texts_path, np.array(self._texts, dtype=object))
        self.metadata_path.write_text(json.dumps(self._metadata), encoding="utf-8")

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Encode text with normalized vectors suitable for cosine similarity."""
        return self.embedder.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True
        ).astype(np.float32)

    def build(self, chunks: List[str] | list[dict]):
        if not chunks:
            self._index = None
            self._texts = []
            self._metadata = []
            for path in (self.index_path, self.texts_path, self.metadata_path):
                if path.exists():
                    path.unlink()
            return
        if isinstance(chunks[0], dict):
            records = chunks
            self._texts = [str(record["content"]) for record in records]
            self._metadata = [
                {
                    "document_id": record.get("document_id"),
                    "source_file": record.get("source_file"),
                    "page_number": record.get("page_number"),
                    "chunk_index": record.get("chunk_index"),
                }
                for record in records
            ]
            if all(record.get("embedding") for record in records):
                embeddings = np.asarray([record["embedding"] for record in records], dtype=np.float32)
            else:
                embeddings = self.embed_texts(self._texts)
        else:
            self._texts = list(chunks)
            self._metadata = [{"source_file": None, "page_number": None, "chunk_index": i} for i in range(len(chunks))]
            embeddings = self.embed_texts(self._texts)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings.astype(np.float32))
        self._index = index
        self._save()

    def retrieve(self, query: str, k: int = 4) -> List[Tuple[str, float]]:
        return [(item["content"], item["score"]) for item in self.retrieve_with_metadata(query, k)]

    def retrieve_with_metadata(self, query: str, k: int = 4) -> list[dict]:
        if self._index is None or not self._texts:
            return []
        q = self.embed_texts([query])
        return self.retrieve_vector_with_metadata(q[0], k)

    def retrieve_vector_with_metadata(self, query_vector: np.ndarray, k: int = 4) -> list[dict]:
        if self._index is None or not self._texts:
            return []
        q = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        scores, idx = self._index.search(q, min(k, len(self._texts)))
        results: list[dict] = []
        for i, score in zip(idx[0], scores[0]):
            if i == -1:
                continue
            results.append({
                "content": self._texts[i],
                "score": float(score),
                **(self._metadata[i] if i < len(self._metadata) else {}),
            })
        return results



