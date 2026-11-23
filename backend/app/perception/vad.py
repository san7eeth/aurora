"""WebRTC VAD with speech-triggered buffering and silence-based endpointing."""

from collections import deque


SAMPLE_RATE = 16_000
FRAME_DURATION_MS = 30
SAMPLES_PER_FRAME = SAMPLE_RATE * FRAME_DURATION_MS // 1000
BYTES_PER_FRAME = SAMPLES_PER_FRAME * 2


class VoiceActivityDetector:
    """Accept 30 ms, mono, 16 kHz signed PCM frames and emit utterances."""

    def __init__(
        self,
        aggressiveness: int = 2,
        silence_frames: int = 20,
        pre_roll_frames: int = 10,
        max_utterance_frames: int = 1000,
    ):
        try:
            import webrtcvad
        except ImportError as exc:
            raise RuntimeError(
                "WebRTC VAD is not installed. Install backend requirements and restart Aurora."
            ) from exc

        if aggressiveness not in range(4):
            raise ValueError("VAD aggressiveness must be between 0 and 3")
        self._vad = webrtcvad.Vad(aggressiveness)
        self.silence_frames = silence_frames
        self.pre_roll = deque(maxlen=pre_roll_frames)
        self.max_utterance_frames = max_utterance_frames
        self._frames: list[bytes] = []
        self._in_speech = False
        self._speech_frames = 0
        self._silence_frames = 0

    def process_frame(self, frame: bytes) -> bytes | None:
        if len(frame) != BYTES_PER_FRAME:
            raise ValueError(f"Expected {BYTES_PER_FRAME} PCM bytes per VAD frame")

        voiced = self._vad.is_speech(frame, SAMPLE_RATE)
        if not self._in_speech:
            self.pre_roll.append(frame)
            if not voiced:
                return None
            self._in_speech = True
            self._frames = list(self.pre_roll)
            self._speech_frames = 1
            self._silence_frames = 0
            return None

        self._frames.append(frame)
        if voiced:
            self._speech_frames += 1
            self._silence_frames = 0
        else:
            self._silence_frames += 1

        if self._silence_frames >= self.silence_frames:
            return self._finish(keep_tail_frames=5)
        if len(self._frames) >= self.max_utterance_frames:
            return self._finish(keep_tail_frames=0)
        return None

    def flush(self) -> bytes | None:
        """Finish the current segment when the client stops recording."""
        if not self._in_speech:
            return None
        return self._finish(keep_tail_frames=5)

    def _finish(self, keep_tail_frames: int) -> bytes | None:
        if self._silence_frames > keep_tail_frames:
            frames = self._frames[: -(self._silence_frames - keep_tail_frames)]
        else:
            frames = self._frames
        audio = b"".join(frames) if self._speech_frames >= 3 else None
        self._frames = []
        self._in_speech = False
        self._speech_frames = 0
        self._silence_frames = 0
        self.pre_roll.clear()
        return audio
