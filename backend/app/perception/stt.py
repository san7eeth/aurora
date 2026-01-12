"""
Whisper-based STT for audio chunk transcription.
"""

from typing import Optional
import io
import tempfile
import os
import subprocess


class WhisperSTT:
    def __init__(self, model_size: str = "tiny"):  # Much faster than "base"
        try:
            import whisper  # type: ignore
        except ImportError:
            self._ready = False
            self._model = None
            return
        
        try:
            self._model = whisper.load_model(model_size)
            self._ready = True
        except Exception:
            self._ready = False
            self._model = None

    @property
    def is_ready(self) -> bool:
        return bool(self._ready and self._model)

    def _convert_with_pydub(self, audio_bytes: bytes) -> Optional[str]:
        """Convert audio bytes to 16kHz mono WAV using pydub.
        Returns the path to the converted WAV or None on failure.
        """
        try:
            from pydub import AudioSegment
            from pydub.utils import which
            
            # Check if ffmpeg is available
            if not which("ffmpeg"):
                print("[STT] ffmpeg not found in PATH")
                return None
            
            # Load audio from bytes
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Convert to 16kHz mono
            audio = audio.set_frame_rate(16000).set_channels(1)
            
            # Save to temp WAV file
            out_fd, out_path = tempfile.mkstemp(suffix=".wav")
            os.close(out_fd)
            
            audio.export(out_path, format="wav")
            return out_path
            
        except Exception as e:
            print(f"[STT] pydub conversion failed: {e}")
            return None

    def transcribe_chunk(self, audio_bytes: bytes) -> Optional[str]:
        if not self._model or not self._ready:
            print(f"[STT] Model not ready: {self._ready}")
            return None
        
        if len(audio_bytes) < 1000:  # Too small, likely not valid audio
            print(f"[STT] Audio too small: {len(audio_bytes)} bytes")
            return None
        
        # First, try to convert via pydub. If not available, try raw bytes as wav.
        wav_path = self._convert_with_pydub(audio_bytes)
        if wav_path is None:
            print("[STT] ffmpeg conversion failed, trying raw WAV")
            # Fallback: assume bytes are already WAV, save and use as-is
            fd, tmp_wav = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            try:
                with open(tmp_wav, "wb") as f:
                    f.write(audio_bytes)
                wav_path = tmp_wav
            except Exception as e:
                print(f"[STT] Failed to write raw WAV: {e}")
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass
                return None
        
        try:
            print(f"[STT] Transcribing {len(audio_bytes)} bytes from {wav_path}")
            # Transcribe with Whisper - optimized for speed
            result = self._model.transcribe(
                wav_path, 
                language="en", 
                fp16=False,
                word_timestamps=False,  # Skip word timestamps for speed
                condition_on_previous_text=False,  # Don't use previous context
                initial_prompt=None,  # No initial prompt
                temperature=0.0  # Deterministic output
            )
            text = result.get("text", "").strip()
            print(f"[STT] Result: '{text}'")
            return text
        except Exception as e:
            print(f"[STT] Whisper transcription failed: {e}")
            return None
        finally:
            try:
                os.remove(wav_path)
            except Exception:
                pass


