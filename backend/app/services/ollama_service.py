"""
Ollama Service — manages Ollama model interactions.
Wraps httpx for async communication with Ollama API.
"""

import logging
from typing import AsyncIterator
import httpx

from ..config import settings

logger = logging.getLogger("aurora.services.ollama")


class OllamaService:
    """Async interface to the Ollama REST API."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Return a list of model names available in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                r.raise_for_status()
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str:
        """Non-streaming generation — returns the full response text."""
        model = model or settings.ollama_model
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "top_p": 0.9,
                            "num_predict": max_tokens,
                        },
                    },
                )
                r.raise_for_status()
                return r.json().get("response", "").strip()
        except httpx.ConnectError:
            return "I'm unable to connect to the local AI model. Please make sure Ollama is running."
        except httpx.TimeoutException:
            return "The AI model took too long to respond. Please try again or use a smaller model."
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            return f"An error occurred while generating a response: {e}"

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """Streaming generation — yields text chunks as they arrive."""
        model = model or settings.ollama_model
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "top_p": 0.9,
                            "num_predict": max_tokens,
                        },
                    },
                ) as response:
                    response.raise_for_status()
                    import json as json_mod
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json_mod.loads(line)
                                token = data.get("response", "")
                                if token:
                                    yield token
                                if data.get("done"):
                                    break
                            except Exception:
                                continue
        except httpx.ConnectError:
            yield "I'm unable to connect to the local AI model. Please make sure Ollama is running."
        except httpx.TimeoutException:
            yield "The AI model took too long to respond. Please try again or use a smaller model."
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"Error: {e}"

    async def model_info(self, model: str | None = None) -> dict | None:
        """Get model metadata from Ollama."""
        model = model or settings.ollama_model
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model},
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None
