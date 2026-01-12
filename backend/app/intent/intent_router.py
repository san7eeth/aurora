"""
Routes messages through RAG and calls Ollama for final answer.
"""

from typing import List
import requests
from ..config import settings


SYSTEM_PROMPT = (
    "You are Aurora, a helpful, privacy-first local assistant. Use provided context to answer."
)


class IntentRouter:
    def __init__(self, ollama_base: str | None = None, model: str | None = None):
        self.base = ollama_base or settings.ollama_base_url
        self.model = model or settings.ollama_model

    def generate(self, prompt: str) -> str:
        url = f"{self.base}/api/generate"
        # Optimized for speed: shorter timeout, no streaming overhead
        resp = requests.post(url, json={
            "model": self.model, 
            "prompt": prompt, 
            "stream": False,
            "options": {
                "temperature": 0.7,  # Slightly faster than higher temps
                "top_p": 0.9,
                "num_predict": 150,  # Limit response length for speed
            }
        }, timeout=30)  # Much shorter timeout
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    def route(self, message: str, retrieved: List[str]) -> str:
        context = "\n\n".join(retrieved[:4]) if retrieved else ""
        prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nUser: {message}\nAssistant:"
        return self.generate(prompt)


