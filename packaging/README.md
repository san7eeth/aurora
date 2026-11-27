# Windows desktop package

## Portable ONEDIR distribution (current implementation)

The user-facing ZIP build is in [`portable/`](portable/). Run `portable/build_release.ps1` on Windows x64 with Python 3.12 and Node.js, then `portable/package_portable.ps1` after setting developer-managed Ed25519 key paths and the independently trusted fingerprint for an official release. `portable/VERSION` supplies the default semantic version. The output is `Aurora-v<version>-Windows-x64-Portable.zip` with one `Aurora/` root, `Aurora.exe`, `Start Aurora.exe`, and a separate `runtime/` directory. An explicitly labelled `-UnsignedCandidate` is available only for internal validation after the clean-checkout gate passes; it is not trusted and cannot be installed by the updater. Never generate a production key in the repository or commit one. See [RELEASE_GUIDE.md](../RELEASE_GUIDE.md) for signing, release publication and clean-VM validation. `portable/README.txt` explains end-user launch and Ollama setup. The existing one-file installer below is a legacy packaging route and is not the primary ZIP strategy.

The current release build uses PyInstaller ONEDIR, which has already been exercised with this dependency set. `portable/nuitka-project.py` is a Nuitka standalone project entry point for evaluation; it is not the production release compiler until it passes the same clean-machine validation. The app executable starts FastAPI, serves the compiled React UI on loopback, and opens the user's browser. It does not add Electron/Tauri or another backend service.

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

## Legacy single-file installer verification status (historical)

Earlier validation built the legacy single-file installer on Windows 11 with Python 3.12.10, PyInstaller 6.22.3, and Inno Setup 7.1.1. It is not evidence for the current portable ONEDIR workflow.

The current ONEDIR validation status is recorded in [`../RELEASE_VALIDATION_REPORT.md`](../RELEASE_VALIDATION_REPORT.md). A clean Windows account/VM test remains pending.

The single-file bundle collects the ML stack and may be large. Sentence Transformer and faster-whisper model weights still download to the user's cache on first use. Measure the built size and startup time on target hardware before release.
