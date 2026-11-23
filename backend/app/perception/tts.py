"""
Offline TTS using pyttsx3. Produces WAV bytes suitable for streaming over WebSocket.
"""

from typing import Optional
import os
import tempfile
import threading


class Pyttsx3TTS:
    def __init__(self, voice: Optional[str] = None, rate: int = 200):  # Faster speech rate
        self._lock = threading.Lock()
        self._rate = max(100, min(300, int(rate)))
        try:
            import pyttsx3  # type: ignore
        except Exception:
            self._ready = False
            self._engine = None
            return
        try:
            self._engine = pyttsx3.init()
        except Exception:
            # Missing SAPI/pywin32 etc.
            self._ready = False
            self._engine = None
            return
        if voice:
            try:
                self._engine.setProperty("voice", voice)
            except Exception:
                pass
        self.set_rate(self._rate)
        self._ready = True

    def set_rate(self, rate: int) -> None:
        self._rate = max(100, min(300, int(rate)))
        if getattr(self, "_engine", None):
            try:
                self._engine.setProperty("rate", self._rate)
            except Exception:
                pass

    @property
    def is_ready(self) -> bool:
        return bool(self._ready)

    def synthesize(self, text: str, rate: int | None = None) -> Optional[bytes]:
        if not self._engine or not self._ready:
            return None
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            with self._lock:
                if rate is not None:
                    self.set_rate(rate)
                self._engine.save_to_file(text, path)
                self._engine.runAndWait()
                with open(path, "rb") as f:
                    return f.read()
        except Exception:
            return None
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
