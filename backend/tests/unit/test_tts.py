"""TTS synthesis writes a nonempty WAV response without initializing the OS voice engine."""
import wave

from app.perception.tts import Pyttsx3TTS


class FakeEngine:
    def save_to_file(self, _text, path):
        with wave.open(path, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(b"\x00\x00" * 160)

    def runAndWait(self):
        pass

    def setProperty(self, *_args):
        pass


def test_synthesize_returns_nonempty_wav_bytes():
    import threading

    tts = Pyttsx3TTS.__new__(Pyttsx3TTS)
    tts._lock = threading.Lock()
    tts._rate = 200
    tts._ready = True
    tts._engine = FakeEngine()
    audio = tts.synthesize("hello")
    assert audio and audio.startswith(b"RIFF") and b"WAVE" in audio[:16]
