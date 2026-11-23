"""STT accepts valid PCM WAV input and returns the recognized transcript."""
from types import SimpleNamespace

import numpy as np

from app.perception.stt import WhisperSTT


class FakeWhisper:
    def transcribe(self, wav_path, **_kwargs):
        import wave

        with wave.open(wav_path, "rb") as source:
            assert source.getframerate() == 16000
            assert source.getnchannels() == 1
            assert source.getsampwidth() == 2
        return [SimpleNamespace(text="recognized locally")], None


def test_transcribe_pcm_creates_wav_and_returns_text():
    recognizer = WhisperSTT.__new__(WhisperSTT)
    recognizer._ready = True
    recognizer._model = FakeWhisper()
    recognizer.last_error = None
    t = np.arange(16000, dtype=np.float32) / 16000
    pcm = (np.sin(2 * np.pi * 200 * t) * 8000).astype("<i2").tobytes()
    assert recognizer.transcribe_pcm(pcm) == "recognized locally"
    assert recognizer.last_error is None
