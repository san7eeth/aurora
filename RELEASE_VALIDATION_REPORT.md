# Aurora Portable Release Validation Report

**Validation date:** 2026-11-27
**Branch:** `fix/release-errors`
**Target:** Windows x64, PyInstaller ONEDIR
**Disposition:** An unsigned engineering candidate is eligible only after all intended changes are committed and the worktree is clean. No ZIP has been generated. No official release is authorized.

## Status summary

| Status | Result |
|---|---|
| PASS | Full backend suite: 120 passed in 25.90s. Three upstream warnings were recorded; pytest-asyncio recognized both configured asyncio options. |
| PASS | PyInstaller ONEDIR v10 build exited 0 on Windows x64 with Python 3.12.10 / PyInstaller 6.22.3. Production frontend assets were already present and frontend building was explicitly skipped for this command. |
| PASS | Frozen `Aurora.exe --self-check` exited 0 after importing FastAPI, FAISS, and SentenceTransformers. |
| PASS | v10 frozen server returned `/health` database `ok`, frontend HTTP 200, native FastAPI WebSocket handshake, and loopback Ollama/model detection. |
| PASS | The frozen server rejected selecting a nonexistent local Ollama model with HTTP 404. |
| PASS | Frozen RAG uploaded and indexed a one-chunk text document; `/api/chat` returned that document as a retrieval source before and after restart. Hugging Face/Transformers offline mode was enabled and the cached embedding model was used. |
| PASS | v10 ONEDIR contained 10,535 files and 77 DLLs, had a frontend entry point, and contained zero loose `.py`, `.pyc`, `.pyo`, `.pyi`, `.db`, `.sqlite`, or `.sqlite3` files. |
| PASS | `git diff --check`, focused launcher tests (9 passed), and PowerShell parser checks passed. |
| PASS | `detect-secrets` scanned 12 reachable Git commits with zero findings. Working-tree results were two false positives, not credentials. |
| FAIL (resolved) | v8 RAG failed because Transformers could not find a runtime `transformers\models` directory. Dependency pinning alone exposed a second source-reload failure in v9; both were fixed and v10 RAG passed. |
| BLOCKED | Authorized external release-signing keys and an independently trusted fingerprint are unavailable. No official signature was created or verified. |
| BLOCKED | The worktree contains intended uncommitted changes. The dirty-checkout gate remains enabled. No candidate ZIP, checksum, extraction audit, or ZIP integrity test has been created. |
| NOT TESTED | Clean Windows 10/11 VM without Python/developer tools. |
| NOT TESTED | ZIP extraction and extracted-candidate self-check, Authenticode, update install, rollback, backup/restore, fully disconnected offline operation, voice/FFmpeg hardware, SmartScreen, or outbound traffic capture. |

## Errors found and fixes

1. **Transformers 4.57 filesystem discovery (v8):** the installed version dynamically walked `transformers\models`, but PyInstaller keeps compiled modules in PYZ and the release excludes `.py` sources. Pinning `transformers==4.44.2` avoids that dynamic package scan; offline development embedding load passed.
2. **Transformers source reload (v9):** `transformers.processing_utils` called `direct_transformers_import()` to reopen `runtime\transformers\__init__.py`, which is intentionally not shipped as source. `desktop_launcher.py` now redirects only that exact frozen Transformers package-root reload to the already loaded package. `aurora.spec` explicitly forces Transformers modules into PYZ, and a focused regression test covers the fallback. The expanded frozen self-check and v10 RAG smoke passed.
3. **Torch config introspection:** the previous frozen workaround accepted `.config` but missed `._config`. The launcher now handles only source-less `torch.*.config` and `torch.*._config` module objects. Focused launcher tests passed.
4. **No OpenMP override:** `KMP_DUPLICATE_LIB_OK` is absent from the launcher and was not used. Frozen FAISS + Torch embedding completed successfully in v10 without an OpenMP duplicate-runtime crash.
5. **pytest asyncio configuration:** `backend/requirements-dev.txt` pins `pytest-asyncio==0.24.0`, which supports `asyncio_mode` and `asyncio_default_fixture_loop_scope`. The full suite reported no unknown-option warnings.

## Commands run and evidence

### Dependency pin and embedding smoke

```powershell
& 'C:\Aurora\backend\.venv\Scripts\python.exe' -m pip install -r 'C:\Aurora\backend\requirements.txt'
```

Result: installed `transformers==4.44.2` and compatible `tokenizers==0.19.1`.

An inline Python smoke loaded `sentence-transformers/all-MiniLM-L6-v2` from the local cache with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`; it returned a normalized embedding of shape `(1, 384)`.

### Focused and complete backend tests

```powershell
& 'C:\Aurora\backend\.venv\Scripts\python.exe' -m pytest 'C:\Aurora\backend\tests\unit\test_portable_launcher.py' -q
```

Result: **9 passed in 1.45s**.

```powershell
Set-Location 'C:\Aurora\backend'
& '.\.venv\Scripts\python.exe' -m pytest -q
```

Result: **120 passed, 3 warnings, 25.90s**. Warnings:

- Starlette: pending deprecation of `multipart` in favor of `python_multipart`.
- Starlette/AnyIO: deprecated `anyio.abc.BlockingPortal` alias.
- Transformers: future change to `clean_up_tokenization_spaces`.

No `asyncio_mode` or `asyncio_default_fixture_loop_scope` warnings appeared.

### Build and frozen checks

```powershell
$buildRoot = Join-Path $env:TEMP 'Aurora-release-build-v10-966f00120f3648a7ab8f4c1506544ab5'
.\packaging\portable\build_release.ps1 -SkipFrontendBuild -OutputRoot $buildRoot
```

Result: **exit 0**. This command reused the existing `frontend/dist`; a fresh `npm ci`, lint, and frontend production build were not executed as part of v10.

```powershell
$exe = Join-Path $buildRoot 'portable-dist\Aurora\Aurora.exe'
$data = Join-Path $env:TEMP 'Aurora-selfcheck-v10-254a0f53bb6b41a6912d2d61a4a0d9df'
& $exe --self-check --data-dir $data
```

Result: **exit 0**. The raw ONEDIR health version was `0.3.0`; packaging copies `packaging\portable\VERSION` (`1.0.0`) beside the executable, but that final ZIP version path is not yet verified.

The frozen server smoke used an isolated temp data directory, a random loopback port, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `OLLAMA_BASE_URL=http://127.0.0.1:11434`, and the installed local `llama3.2:3b` model. Observed output:

```text
HEALTH_DATABASE=PASS
FRONTEND_HTTP_200=PASS
OLLAMA_LOCAL_MODEL_DETECTED=PASS
MISSING_MODEL_REJECTED=PASS
FASTAPI_WEBSOCKET_HANDSHAKE=PASS
FROZEN_DOCUMENT_INGESTION=PASS ... "chunks": 1 ... "status": "indexed"
FROZEN_RAG_RETRIEVAL=PASS ... "source_file": "aurora-frozen-rag-verification.txt"
GRACEFUL_SHUTDOWN=PASS
DOCUMENT_PERSISTENCE_AFTER_RESTART=PASS
FROZEN_RAG_RETRIEVAL_AFTER_RESTART=PASS ... "source_file": "aurora-frozen-rag-verification.txt"
```

The only configured inference endpoint was loopback Ollama, and Hugging Face downloads were disabled. This test did not capture all process traffic, so it is not proof of no outbound connections.

The v10 `warn-aurora.txt` contains **1,139 lines, 352 missing-module entries, and 349 unique missing names**. The build log contains **70 nonfatal missing-hidden-import errors**, all under the optional Torch distributed checkpoint, sharded-tensor, and sharding-spec areas. The actual Windows Torch `torch.utils.data.dataloader` imports core `torch.distributed`; that core namespace was retained. Aurora has no application-source imports of `einops`, TensorBoard, TensorFlow, or Socket.IO; frozen RAG passed without relying on those optional components.

Other nonfatal warning classes include optional platform/tooling modules (for example `IPython`, `matplotlib`, `pandas`, `torch_xla`, `aiohttp`, and database drivers), optional `tensorboardX`/TensorFlow integrations, and generated `pycparser.lextab`/`yacctab` tables. These optional features are not part of Aurora's portable inference path and were not individually tested. The missing distributed submodule warnings remain visible in the build output; they were not suppressed or treated as successful imports.

### Secrets and local database

`gitleaks` and `detect-secrets` were initially unavailable. `detect-secrets==1.5.0` was installed in a temporary venv, not added to project dependencies. The final source-tree scan command was:

```powershell
detect-secrets scan --all-files --no-verify `
  --exclude-files '(^|[\\/])(\.git|\.venv|\.pytest_cache|node_modules|dist|build|release)([\\/]|$)' .
```

It found:

- `RELEASE_GUIDE.md`: example fingerprint placeholder false positive, not a key or credential.

An earlier broad scan also included the ignored `.pytest_cache` and flagged `backend\.pytest_cache\CACHEDIR.TAG`, a high-entropy marker false positive. The history scan ran `git rev-list --all` (**12 commits**) and archived/scanned each commit using `detect-secrets scan --all-files --no-verify`; output: `HISTORY_FINDINGS=0`. This is a detector result, not a guarantee against every secret format.

The full backend suite includes release-security unit tests that generate ephemeral fixture keys under pytest's temporary directories to exercise verification code. These were test-only fixtures, not developer/release keys; no key was placed in the repository or release output, and no official package was signed.

The local `backend\data\aurora.db` passed SQLite `PRAGMA quick_check` (`ok`) and contains 5 conversations, 4 messages, 1 memory, 2 settings, and 0 documents. The DB is staged for deletion from the next tree, but its local file was retained. It exists in Git history; deleting the current tracked copy does not purge prior commits. No history rewrite was performed.

## Packaging, signing, and Git status

`package_portable.ps1` checks `git status --porcelain --untracked-files=all` and refuses to proceed before creating output if the checkout is dirty. This gate was not disabled. An unsigned-candidate attempt returned:

```text
DIRTY_GATE_REJECTION=Commit all intended source changes and resolve unrelated changes before packaging.
OUTPUT_ROOT_CREATED=False
AURORA_RELEASE_PRIVATE_KEY=UNSET
AURORA_RELEASE_PUBLIC_KEY=UNSET
AURORA_RELEASE_KEY_FINGERPRINT=UNSET
```

The current worktree changes are listed in [PORTABLE_RELEASE_CHECKLIST.md](./PORTABLE_RELEASE_CHECKLIST.md); review and commit intended changes in the requested groups before packaging.

The v10 ONEDIR is a build result, **not** a portable ZIP. No package checksum, ZIP CRC result, extraction test, or archive-member audit exists yet. Do not describe the candidate as signed or trusted.

The candidate command, to be run only after a clean commit, is:

```powershell
$buildRoot = Join-Path $env:TEMP 'Aurora-release-build-v10-966f00120f3648a7ab8f4c1506544ab5'
$candidateRoot = Join-Path $env:TEMP ('Aurora-UNSIGNED-RC-' + [guid]::NewGuid().ToString('N'))
.\packaging\portable\package_portable.ps1 `
  -UnsignedCandidate `
  -OutputRoot $candidateRoot `
  -DistributionPath (Join-Path $buildRoot 'portable-dist\Aurora') `
  -ToolsDirectory (Join-Path $buildRoot 'portable-tools')
```

Expected output name: `Aurora-v1.0.0-Windows-x64-Portable-UNSIGNED-RC.zip`. This command has **not** been run. After generation, verify its `.sha256`, ZIP CRC, `UNSIGNED-RC` manifest, extracted structure, and prohibited-file list, then run the extracted executable's `--self-check` in a new short path.

No authorized release keys or independently trusted fingerprint were available. Do not run the signed packaging path, publish a release, or use an unsigned candidate with the updater.

## Clean-machine and remaining blockers

`Test-PortableRelease.ps1` was not run: it requires a signed ZIP, an independently obtained trusted fingerprint/public key, and a clean Windows 10/11 x64 VM. The available Windows 11 build host has Python and developer tools. Clean-VM startup, ZIP verification/tampering, updater installation, user confirmation, rollback, data backup/restore, offline disconnected operation, voice/FFmpeg hardware, SmartScreen behavior, and outbound traffic observation remain **NOT TESTED**.

The portable README explains that Ollama and models are not bundled, Ollama inference is local, first-use model downloads require network unless cached, and Linux/macOS require separate builds. Full offline operation on a clean machine with no cached models is not verified.

## Files changed in the validation worktree

Tracked modifications: `.github/workflows/release.yml`, `ARCHITECTURE.md`, `CHANGELOG.md`, `DEPLOYMENT_GUIDE.md`, `DEVELOPMENT_PROGRESS.md`, `DEVELOPMENT_ROADMAP.md`, `LEARNING_NOTES.md`, `README.md`, `SECURITY.md`, `TESTING_GUIDE.md`, `backend/app/api.py`, `backend/app/core/config.py`, `backend/app/core/runtime_paths.py`, `backend/app/intent/load_documents.py`, `backend/app/intent/rag_service.py`, `backend/desktop_launcher.py`, `backend/pytest.ini`, `backend/requirements-dev.txt`, `backend/requirements.txt`, and `packaging/README.md`.

Added: `PORTABLE_RELEASE_CHECKLIST.md`, `RELEASE_GUIDE.md`, `RELEASE_VALIDATION_REPORT.md`, `Test-PortableRelease.ps1`, three portable/release-security backend unit-test files, and the portable build/package scripts, spec, resources, changelog, version, user README, verifier, backup/restore/update/rollback scripts, and packaging requirements. `packaging/portable/nuitka-project.py` is developer-only and is not the active release path.

Staged deletion: `backend/data/aurora.db`. The local database file remains on disk and was not copied into the ONEDIR.
