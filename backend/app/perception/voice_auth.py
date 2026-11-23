"""Compact local speaker-profile features for opt-in voice matching.

This is a convenience speaker match, not a security-grade biometric authenticator.
"""

import numpy as np


def voice_embedding(pcm_bytes: bytes, sample_rate: int = 16000) -> list[float]:
    if sample_rate != 16000 or len(pcm_bytes) < sample_rate * 2:
        raise ValueError("Record at least one second of 16 kHz mono PCM audio")
    audio = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) / 32768.0
    audio = audio - audio.mean()
    if np.max(np.abs(audio)) < 0.008:
        raise ValueError("Audio is too quiet to build a voice profile")
    audio = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])
    frame_length, hop = 400, 160
    if len(audio) < frame_length:
        raise ValueError("Audio sample is too short")
    frames = np.lib.stride_tricks.sliding_window_view(audio, frame_length)[::hop]
    spectrum = np.abs(np.fft.rfft(frames * np.hamming(frame_length), n=512)) ** 2
    # Broad log-frequency bands capture vocal resonance without retaining speech.
    edges = np.unique(np.geomspace(2, spectrum.shape[1], 25).astype(int))
    bands = np.stack([np.log1p(spectrum[:, edges[i]:edges[i + 1]].mean(axis=1)) for i in range(len(edges) - 1)], axis=1)
    features = np.concatenate([bands.mean(axis=0), bands.std(axis=0)])
    norm = np.linalg.norm(features)
    if norm == 0:
        raise ValueError("Could not extract a voice profile from this sample")
    return (features / norm).astype(float).tolist()


def similarity(first: list[float], second: list[float]) -> float:
    if len(first) != len(second) or not first:
        return 0.0
    return float(np.clip(np.dot(first, second), -1.0, 1.0))
