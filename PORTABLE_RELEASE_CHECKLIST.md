# Aurora Portable Release Checklist

**Validation date:** 2026-11-27
**Branch:** `fix/release-errors`
**Release mode:** PyInstaller ONEDIR only
**Disposition:** No ZIP was generated. Signing is blocked and clean-Windows-VM validation remains open.

## Status

| Requirement | Status | Evidence / limitation |
|---|---|---|
| Windows x64 PyInstaller ONEDIR build | PASS | `build_release.ps1 -SkipFrontendBuild -OutputRoot ...` completed with exit 0. Build used the existing production `frontend/dist`. |
| Frozen self-check | PASS | v10 `Aurora.exe --self-check --data-dir <isolated path>` exited 0; check now imports `sentence_transformers` as well as FastAPI and FAISS. |
| Runtime payload and source exclusion | PASS | ONEDIR contained `Aurora.exe`, `runtime/`, frontend `index.html`, 10,535 files and 77 DLLs; zero loose `.py`, `.pyc`, `.pyo`, `.pyi`, `.db`, `.sqlite`, or `.sqlite3` files. |
| Frozen server, frontend, database, WebSocket | PASS | `/health` database `ok`, frontend HTTP 200, FastAPI `/ws` handshake, graceful shutdown, restart, and database persistence all passed. The application uses native FastAPI WebSockets, not Socket.IO. |
| Frozen local Ollama/model handling | PASS | Local Ollama at `127.0.0.1:11434` reported `llama3.2:3b`; selecting a nonexistent local model returned HTTP 404. No cloud model endpoint was configured. |
| Frozen FAISS/RAG ingestion and retrieval | PASS | Uploaded a temporary text document; response was `status=indexed`, one chunk. `/api/chat` returned the uploaded filename as a retrieval source, both before and after restart. Hugging Face/Transformers offline flags were enabled and the cached embedding model was used. |
| Full backend suite | PASS | `python -m pytest -q`: 120 passed in 25.90s. Three upstream warnings remain; no unknown pytest-asyncio options were reported. |
| Secret scan, reachable Git history | PASS | `detect-secrets` scanned 12 reachable commits; zero findings. Working-tree scan reported two non-secret false positives: ignored `.pytest_cache\CACHEDIR.TAG` and the documented fingerprint placeholder in `RELEASE_GUIDE.md`. |
| Dirty-checkout package gate | PASS / BLOCKED | An unsigned-candidate attempt was rejected with `Commit all intended source changes and resolve unrelated changes before packaging.` The output root was not created. Worktree changes must be committed before packaging. |
| Official signing | BLOCKED | No authorized external key pair or independently trusted fingerprint is available. Do not generate a release key or sign an official package. |
| Clean Windows 10/11 VM | NOT TESTED | The available host has Python and developer tools. `Test-PortableRelease.ps1` was not run. |
| Update, rollback, backup/restore, traffic capture, full offline, voice/FFmpeg | NOT TESTED | These require the clean VM, authorized signed ZIP, user confirmation, or audio hardware. |

## Commands and evidence

Run from the repository root unless noted.

```powershell
Set-Location C:\Aurora\backend
& .\.venv\Scripts\python.exe -m pytest -q
```

Result: **120 passed, 3 warnings, 25.90s**. Warnings were Starlette's `python_multipart` pending deprecation, AnyIO's deprecated `BlockingPortal` alias, and Transformers' `clean_up_tokenization_spaces` future deprecation. `backend/requirements-dev.txt` pins `pytest-asyncio==0.24.0`; both `asyncio_mode` and `asyncio_default_fixture_loop_scope` were accepted.

```powershell
$buildRoot = Join-Path $env:TEMP 'Aurora-release-build-v10-966f00120f3648a7ab8f4c1506544ab5'
.\packaging\portable\build_release.ps1 -SkipFrontendBuild -OutputRoot $buildRoot
```

Result: **exit 0**. `-SkipFrontendBuild` used the existing `frontend/dist`; a complete fresh npm/frontend build was not part of this v10 command. The ONEDIR audit found 10,535 files, 77 DLLs, the production frontend entry point, and zero loose source/bytecode/database files. The raw build reports version `0.3.0` until the packager places the release `VERSION` beside `Aurora.exe`; a ZIP with its final version file has not yet been tested.

```powershell
$exe = Join-Path $buildRoot 'portable-dist\Aurora\Aurora.exe'
$data = Join-Path $env:TEMP 'Aurora-selfcheck-v10-254a0f53bb6b41a6912d2d61a4a0d9df'
& $exe --self-check --data-dir $data
```

Result: **exit 0**.

Frozen server smoke used an isolated temp data directory, a random loopback port, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and `OLLAMA_BASE_URL=http://127.0.0.1:11434`. Output:

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

The local Ollama model generated the chat response. The test did not invoke a cloud AI service; network traffic was not captured, so this is not a traffic-observation result.

`git diff --check` passed. PowerShell parser checks passed for `build_release.ps1`, `package_portable.ps1`, `generate_checksums.ps1`, `verify_release.ps1`, and `Test-PortableRelease.ps1`.

## Defects found and fixes

1. A v8 frozen RAG upload failed because Transformers 4.57 dynamically scanned a `transformers\models` source tree that is intentionally absent from the source-free ONEDIR. `backend/requirements.txt` now pins the compatible `transformers==4.44.2`; offline development embedding load passed.
2. The first v9 frozen upload then failed when Transformers 4.44's `direct_transformers_import()` tried to reopen `runtime\transformers\__init__.py`. PyInstaller's Transformers hook requests source-on-disk collection, but portable output excludes `.py`. The launcher now redirects only that exact frozen package-root reload to the already loaded Transformers package, and the spec forces Transformers modules into PYZ. A regression test covers the narrow fallback. v10 self-check and frozen RAG ingestion/retrieval passed.
3. A prior Torch fallback handled `.config` but not `._config` module names. The fallback now accepts only source-less `torch.*.config` and `torch.*._config` module objects; launcher regression tests cover both.
4. `KMP_DUPLICATE_LIB_OK` is not set. The v10 real FAISS + Torch embedding test completed without an OpenMP duplicate-runtime abort; do not add that environment workaround.

## Build warnings and disposition

The v10 `warn-aurora.txt` contains 1,139 lines and 352 missing-module entries (349 unique names), mostly optional dependencies, platform-specific modules, or development-only packages. The build log contains 70 nonfatal missing-hidden-import errors for unavailable Torch distributed checkpoint, sharded-tensor, and sharding-spec submodules. These features are not used by Aurora's inference path; the installed `torch.utils.data.dataloader` imports core `torch.distributed`, which remains included, and the frozen RAG test passed.

- `einops`, TensorBoard/TensorBoardX, TensorFlow, and their integrations are optional; no Aurora application source imports them. They remain excluded/not required.
- Optional `matplotlib`, `pandas`, IPython/Jupyter, `torch_xla`, `aiohttp`, and database-driver imports are not Aurora runtime requirements.
- `pycparser.lextab` and `pycparser.yacctab` are optional generated grammar tables.
- Windows-unavailable or optional distributed backend modules remain warnings; no core runtime failure was observed.
- These warning dispositions are based on source audit plus frozen runtime smoke tests. Distributed checkpoint, plotting, and optional TensorFlow features are not supported or tested.

## Secret and local-data checks

The broad working-tree scan used `detect-secrets scan --all-files --no-verify` and reported the ignored pytest cache marker and example release-fingerprint placeholder; neither is a credential. A final source scan excluding `.git`, `.venv`, `.pytest_cache`, `node_modules`, `dist`, `build`, and `release` reported only the fingerprint placeholder. A history scan used `git archive` for each revision from `git rev-list --all`; **12 commits scanned, zero findings**.

The local `backend/data/aurora.db` passed SQLite `PRAGMA quick_check` (`ok`). It contains 5 conversations, 4 messages, 1 memory, 2 settings, and 0 documents. The DB is staged for deletion from the next tree while the local file remains. It exists in Git history; deleting the current tracked copy does not purge it. Do not rewrite shared history without an authorized maintainer decision.

## Required next steps and commands

1. Review and commit intended changes in the requested logical groups: source/tests, packaging/workflow, documentation, then the staged database deletion. Do not stage `.env`, databases, keys, user data, build output, or release output.
2. Confirm `git status --short --untracked-files=all` is empty. The packaging gate must remain enabled.
3. From the clean committed checkout, create an unsigned engineering candidate only (not an official/trusted release):

   ```powershell
   $buildRoot = Join-Path $env:TEMP 'Aurora-release-build-v10-966f00120f3648a7ab8f4c1506544ab5'
   $candidateRoot = Join-Path $env:TEMP ('Aurora-UNSIGNED-RC-' + [guid]::NewGuid().ToString('N'))
   .\packaging\portable\package_portable.ps1 `
     -UnsignedCandidate `
     -OutputRoot $candidateRoot `
     -DistributionPath (Join-Path $buildRoot 'portable-dist\Aurora') `
     -ToolsDirectory (Join-Path $buildRoot 'portable-tools')
   ```

4. Verify the generated `.sha256`, ZIP CRC, `UNSIGNED-RC` manifest/filename, extracted `Aurora.exe` and `runtime\`, and absence of `.py`, `.pyc`, `.db`, and `.env` members. Extract to a new short path and run the extracted executable's `--self-check`. Do not run the signed-release verifier against this candidate or use it for updates.
5. Before any official release, obtain authorized external Ed25519 keys and an independently published fingerprint. Run the signed package verifier and `Test-PortableRelease.ps1` only on a clean Windows 10/11 x64 VM with a signed ZIP and trusted public key.
6. On the clean VM, record startup, frontend, WebSocket, Ollama/model present and missing, RAG, voice/FFmpeg, data persistence/update, offline behavior, backup/restore, rollback, integrity rejection, SmartScreen, and outbound traffic observations. These remain untested here.

## Changed paths in this validation worktree

Tracked modifications: `.github/workflows/release.yml`, `ARCHITECTURE.md`, `CHANGELOG.md`, `DEPLOYMENT_GUIDE.md`, `DEVELOPMENT_PROGRESS.md`, `DEVELOPMENT_ROADMAP.md`, `LEARNING_NOTES.md`, `README.md`, `SECURITY.md`, `TESTING_GUIDE.md`, `backend/app/api.py`, `backend/app/core/config.py`, `backend/app/core/runtime_paths.py`, `backend/app/intent/load_documents.py`, `backend/app/intent/rag_service.py`, `backend/desktop_launcher.py`, `backend/pytest.ini`, `backend/requirements-dev.txt`, `backend/requirements.txt`, and `packaging/README.md`.

Added paths: `PORTABLE_RELEASE_CHECKLIST.md`, `RELEASE_GUIDE.md`, `RELEASE_VALIDATION_REPORT.md`, `Test-PortableRelease.ps1`, `backend/tests/unit/test_portable_launcher.py`, `backend/tests/unit/test_portable_runtime_paths.py`, `backend/tests/unit/test_release_security.py`, `packaging/portable/CHANGELOG.md`, `packaging/portable/README.txt`, `packaging/portable/VERSION`, `packaging/portable/aurora.spec`, `packaging/portable/build_release.ps1`, `packaging/portable/generate_checksums.ps1`, `packaging/portable/nuitka-project.py` (not active), `packaging/portable/package_portable.ps1`, `packaging/portable/release_security.py`, `packaging/portable/requirements-packaging.txt`, `packaging/portable/resources/LICENSE.txt`, `packaging/portable/resources/aurora.env.example`, `packaging/portable/scripts/Backup-AuroraData.ps1`, `Restore-AuroraData.ps1`, `Rollback-Aurora.ps1`, `Update-Aurora.ps1`, `Verify-Release.ps1`, `packaging/portable/start_aurora.py`, `packaging/portable/verify_release.ps1`, and `packaging/portable/verify_release.py`.

Staged deletion: `backend/data/aurora.db`; the local database file was retained and was not included in build output.
