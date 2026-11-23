"""
IntentRouter — calls Ollama with conversation history and RAG context.
Phase 2: Conversation history support, configurable params, better error handling.
"""

from typing import List, Dict
import requests
from ..config import settings

SYSTEM_PROMPT = (
    "You are Aurora, a helpful, privacy-first local AI assistant. "
    "You run entirely on the user's own machine — no data leaves their device. "
    "Use the provided context to give accurate, grounded answers. "
    "Be concise but thorough. If you don't know something, say so honestly."
)


class IntentRouter:
    def __init__(
        self,
        ollama_base: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ):
        self.base = ollama_base or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @property
    def _model(self) -> str:
        # Always read from settings so runtime model switching is reflected
        return settings.ollama_model

    def _build_prompt(self, message: str, context: List[str], history: List[Dict[str, str]]) -> str:
        parts = [SYSTEM_PROMPT]

        if context:
            parts.append("\n\n--- Relevant Knowledge ---")
            for i, chunk in enumerate(context[:4], 1):
                parts.append(f"[{i}] {chunk.strip()}")
            parts.append("--- End of Knowledge ---")

        if history:
            parts.append("\n\n--- Conversation History ---")
            for turn in history[-10:]:  # Last 5 exchanges (10 messages)
                role = "User" if turn["role"] == "user" else "Aurora"
                parts.append(f"{role}: {turn['content']}")
            parts.append("--- End of History ---")

        parts.append(f"\nUser: {message}\nAurora:")
        return "\n".join(parts)

    def generate(self, prompt: str) -> str:
        url = f"{self.base}/api/generate"
        try:
            resp = requests.post(
                url,
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "top_p": 0.9,
                        "num_predict": self.max_tokens,
                    },
                },
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            return "I'm unable to connect to the local AI model right now. Please make sure Ollama is running."
        except requests.exceptions.Timeout:
            return "The AI model took too long to respond. Please try again or use a smaller model."
        except Exception as e:
            return f"An error occurred while generating a response: {e}"

    def route(self, message: str, context: List[str], history: List[Dict[str, str]] | None = None) -> str:
        prompt = self._build_prompt(message, context, history or [])
        return self.generate(prompt)
