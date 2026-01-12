"""
FAISS vector store + sentence-transformers embeddings + simple retrieval.
"""

from typing import List, Tuple
from pathlib import Path
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
        self._index: faiss.IndexFlatIP | None = None
        self._texts: List[str] = []
        self._load()

    def _load(self):
        if self.index_path.exists() and self.texts_path.exists():
            self._index = faiss.read_index(str(self.index_path))
            self._texts = np.load(self.texts_path, allow_pickle=True).tolist()

    def _save(self):
        if self._index is not None:
            faiss.write_index(self._index, str(self.index_path))
        np.save(self.texts_path, np.array(self._texts, dtype=object))

    def build(self, chunks: List[str]):
        if not chunks:
            self._index = None
            self._texts = []
            return
        embeddings = self.embedder.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings.astype(np.float32))
        self._index = index
        self._texts = chunks
        self._save()

    def retrieve(self, query: str, k: int = 4) -> List[Tuple[str, float]]:
        if self._index is None or not self._texts:
            return []
        q = self.embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        scores, idx = self._index.search(q, min(k, len(self._texts)))
        results: List[Tuple[str, float]] = []
        for i, score in zip(idx[0], scores[0]):
            if i == -1:
                continue
            results.append((self._texts[i], float(score)))
        return results



