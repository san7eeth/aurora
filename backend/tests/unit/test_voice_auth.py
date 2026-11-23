"""Unit checks for ephemeral PCM feature extraction and local speaker similarity."""

import numpy as np
import pytest

from app.perception.voice_auth import similarity, voice_embedding


def _tone_pcm(frequency: float = 190.0) -> bytes:
    time = np.arange(16000, dtype=np.float32) / 16000
    signal = 0.2 * np.sin(2 * np.pi * frequency * time)
    return (signal * 32767).astype("<i2").tobytes()


def test_voice_embedding_is_normalized_and_finite():
    vector = voice_embedding(_tone_pcm())
    assert len(vector) >= 30
    assert np.isclose(np.linalg.norm(vector), 1.0)
    assert np.isfinite(vector).all()


def test_matching_identical_profile_has_unit_similarity():
    vector = voice_embedding(_tone_pcm())
    assert similarity(vector, vector) == pytest.approx(1.0)


def test_voice_embedding_rejects_short_audio():
    with pytest.raises(ValueError, match="one second"):
        voice_embedding(b"\x00\x00" * 100)


def test_voice_auth_api_enroll_verify_and_reject_invalid_sample(test_client):
    sample = _tone_pcm()
    enrolled = test_client.post("/api/voice-auth/enroll", content=sample)
    assert enrolled.status_code == 200
    assert test_client.get("/api/voice-auth/status").json()["enrolled"] is True

    matched = test_client.post("/api/voice-auth/verify", content=sample)
    assert matched.status_code == 200
    assert matched.json()["matched"] is True

    rejected = test_client.post("/api/voice-auth/verify", content=b"\x00\x00" * 100)
    assert rejected.status_code == 400

    deleted = test_client.delete("/api/voice-auth/profile")
    assert deleted.status_code == 200
    assert test_client.get("/api/voice-auth/status").json()["enrolled"] is False
