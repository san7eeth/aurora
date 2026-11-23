# Windows desktop package

Phase 10 uses the roadmap's recommended PyInstaller route. It ships one `Aurora.exe` that starts FastAPI, serves the compiled React UI on loopback, and opens the user's browser. It does not add Electron/Tauri or another backend service.

## Requirements

- Windows x64, Python 3.12, Node.js, and the backend/frontend dependencies.
- PyInstaller 6.22.3, pinned in `backend/requirements-packaging.txt`.
- Inno Setup 7 to compile the installer. The `.iss` file is also compatible with Inno Setup 6.
- Ollama installed and running on the host, with a model available. Ollama and LLM weights are not bundled.

Install the packager in the existing backend environment and install Inno Setup if needed:

```powershell
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-packaging.txt
winget install --id JRSoftware.InnoSetup.7 -e -s winget -i
```

The Inno Setup command starts its interactive installer. It is an independent Windows build tool; it is not installed automatically by Aurora.

## Build

From the repository root:

```powershell
./packaging/windows/Build-WindowsPackage.ps1 -Version 0.3.0
```

The script installs the frontend lockfile dependencies, runs the production Vite build, creates a PyInstaller one-file executable, assembles the runnable package, then invokes Inno Setup when available.

- Runnable package: `release/Aurora/`
- PyInstaller output: `release/pyinstaller/Aurora.exe`
- Setup installer: `release/installer/Aurora-Setup-0.3.0-x64.exe`

Pass `-SkipInstallerCompile` to prepare the runnable folder without Inno Setup. The executable still requires a successful PyInstaller build.
Pass `-SkipFrontendBuild` when `frontend/dist` is already a verified production build; this uses the existing bundle and avoids reinstalling frontend dependencies.

## Run and stop

Use `release/Aurora/Start-Aurora.ps1` or the installer shortcut. The server binds to `127.0.0.1:8000` and opens `http://127.0.0.1:8000/`. To stop gracefully, run `release/Aurora/Stop-Aurora.ps1`; the stop request shuts down Uvicorn and leaves user data intact.

Packaged writable data is stored under `%LOCALAPPDATA%\Aurora`:

- `aurora.db` — SQLite state.
- `docs/` — uploaded documents.
- `vectorstore/` — local retrieval index.
- `models/huggingface/` — model cache used by voice and embedding features.
- `logs/aurora.log` — backend diagnostics.

The installer is per-user and does not require administrator rights. Uninstall requests a clean server shutdown and preserves user data.

## Current verification status

Built on Windows 11 with Python 3.12.10, PyInstaller 6.22.3, and Inno Setup 7.1.1. `release/pyinstaller/Aurora.exe` (about 358 MB) and `release/installer/Aurora-Setup-0.3.0-x64.exe` (about 355 MB) were produced. The executable served `/` with the compiled frontend, returned a healthy database status and one model from `/api/models`, and shut down cleanly on an isolated data directory and port. The installer compiled without warnings, installed into a temporary folder, placed its expected files, and uninstalled successfully.

The clean Windows account/VM install and uninstall test remains pending. The smoke test also did not exercise chat WebSockets, voice hardware, first-run model downloads, or a machine without Python/Node. Phase 10 remains open until the clean-system check passes.

The single-file bundle collects the ML stack and may be large. Sentence Transformer and faster-whisper model weights still download to the user's cache on first use. Measure the built size and startup time on target hardware before release.
