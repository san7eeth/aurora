"""
WhisperSTT using faster-whisper — faster inference, better Windows/Python 3.12 compat.
Runs in a thread pool via asyncio.to_thread() — never called directly in async context.
"""

from typing import Optional
import io
import tempfile
import os


class WhisperSTT:
    def __init__(self, model_size: str = "tiny"):
        self._ready = False
        self._model = None
        try:
            from faster_whisper import WhisperModel
            # Use CUDA if available, else CPU with int8 for speed
            try:
                self._model = WhisperModel(model_size, device="cuda", compute_type="float16")
            except Exception:
                self._model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self._ready = True
        except ImportError:
            print("[STT] faster-whisper not installed")
        except Exception as e:
            print(f"[STT] Failed to load Whisper model: {e}")

    @property
    def is_ready(self) -> bool:
        return bool(self._ready and self._model)

    def _convert_with_pydub(self, audio_bytes: bytes) -> Optional[str]:
        """Convert audio bytes to 16kHz mono WAV using pydub + ffmpeg."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            audio = audio.set_frame_rate(16000).set_channels(1)
            fd, out_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            audio.export(out_path, format="wav")
            return out_path
        except Exception as e:
            print(f"[STT] pydub conversion failed: {e}")
            return None

    def transcribe_chunk(self, audio_bytes: bytes) -> Optional[str]:
        if not self.is_ready:
            print("[STT] Model not ready")
            return None
        if len(audio_bytes) < 1000:
            return None

        wav_path = self._convert_with_pydub(audio_bytes)
        if wav_path is None:
            # Fallback: treat as raw WAV
            fd, wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with open(wav_path, "wb") as f:
                f.write(audio_bytes)

        try:
            segments, _ = self._model.transcribe(
                wav_path,
                language="en",
                beam_size=1,
                word_timestamps=False,
                condition_on_previous_text=False,
                temperature=0.0,
            )
            text = " ".join(seg.text for seg in segments).strip()
            print(f"[STT] Transcript: '{text}'")
            return text if text else None
        except Exception as e:
            print(f"[STT] Transcription failed: {e}")
            return None
        finally:
            try:
                os.remove(wav_path)
            except Exception:
                pass
