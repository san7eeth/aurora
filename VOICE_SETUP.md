# Voice setup

Install the backend dependencies from `backend/requirements.txt`, then start Aurora. Voice capture sends 16 kHz mono PCM frames from the browser to WebRTC VAD; the normal voice path writes WAV directly for faster-whisper and does not require FFmpeg.

Allow microphone access in the browser. The Voice screen's **Voice settings** panel lets you choose an input device and set speech output rate (100–300). Device names may appear after microphone permission is granted.

Aurora still accepts legacy encoded audio uploads through pydub. That fallback requires **FFmpeg** on `PATH`:

Check whether FFmpeg is available from the same terminal used to start Aurora:

```powershell
ffmpeg -version
```

If PowerShell reports that `ffmpeg` is not recognized, install FFmpeg using your preferred Windows package source, add its `bin` directory to `PATH`, then open a new terminal and repeat the check. Restart Aurora after changing `PATH`. Text chat, PCM voice recognition, and text-to-speech do not require FFmpeg.
