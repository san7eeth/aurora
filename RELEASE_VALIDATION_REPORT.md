# Aurora Portable Release Validation Report

**Validation date:** 2026-11-28
**Branch:** `fix/release-errors`
**Target:** Windows x64, PyInstaller ONEDIR
**Disposition:** The existing v10 unsigned candidate passed archive checks but failed grounded RAG generation. An intermediate v11 temperature-only change also failed repeat testing. The explicit prompt fix passed focused tests and cold-cache API/browser RAG checks in a rebuilt local v12 ONEDIR; no replacement ZIP was packaged. The unsigned candidate remains v10. No build is signed or authorized for publication.

## Status summary

| Status | Result |
|---|---|
| PASS | Full backend suite: 120 passed in 25.90s. Three upstream warnings were recorded; pytest-asyncio recognized both configured asyncio options. |
| PASS | PyInstaller ONEDIR v10 build exited 0 on Windows x64 with Python 3.12.10 / PyInstaller 6.22.3. Production frontend assets were already present and frontend building was explicitly skipped for this command. |
| PASS | Frozen `Aurora.exe --self-check` exited 0 after importing FastAPI, FAISS, and SentenceTransformers. |
| PASS | v10 frozen server returned `/health` database `ok`, frontend HTTP 200, native FastAPI WebSocket handshake, and loopback Ollama/model detection. |
| PASS | The frozen server rejected selecting a nonexistent local Ollama model with HTTP 404. |
| PASS (retrieval only) | v10 froze and indexed a one-chunk text document and returned its citation; this did not prove grounded generation. Earlier cached/offline retrieval smoke passed. See the RAG generation failure and fix below. |
| PASS | v10 ONEDIR contained 10,535 files and 77 DLLs, had a frontend entry point, and contained zero loose `.py`, `.pyc`, `.pyo`, `.pyi`, `.db`, `.sqlite`, or `.sqlite3` files. |
| PASS | `git diff --check`, focused launcher tests (9 passed), and PowerShell parser checks passed. |
| PASS | `detect-secrets` scanned 12 reachable Git commits with zero findings. Working-tree results were two false positives, not credentials. |
| PASS | Intended source/tests, packaging/workflow, and documentation were committed in logical groups; the local database tracking removal is commit `49c3be3`. `git status --short --untracked-files=all` was empty before packaging. |
| PASS | Unsigned candidate `Aurora-v1.0.0-Windows-x64-Portable-UNSIGNED-RC.zip` generated with the dirty-checkout gate enabled. The candidate manifest identifies release `v1.0.0-1626f0157295-UNSIGNED-RC`. |
| PASS | Sidecar SHA-256 matched (`38295fdc0e6f027c1bf8b16e3e3a67d0a21a3ca7b9a8432cc04ff06f2bc631b8`); independent manifest verification and ZIP CRC passed. Archive has 10,550 members under one `Aurora/` root and no `.py`, `.pyc`, `.pyo`, `.pyi`, `.db`, `.sqlite`, `.sqlite3`, or `.env` members. |
| PASS | Extracted to a fresh temporary directory; required launcher, runtime, frontend, resources, scripts, version, checksum list, and manifest were present. Extracted tree had zero prohibited source/database/environment files; `Aurora.exe --self-check` exited 0 with an isolated data directory. |
| PASS (source/v12; v10/v11 FAIL) | v10 and temperature-only v11 repeatedly ignored relevant retrieved context. The v12 prompt fix retained the configured temperature; three cold-cache API answers and a Playwright Chat answer used the fact and its citation. |
| PASS | New local v12 PyInstaller ONEDIR built without a frontend rebuild; `--self-check`, three grounded RAG API answers, citations, and a Playwright RAG chat passed. The existing v10 ZIP was not changed or repackaged. |
| PASS | Playwright checked all eight screens, theme switching, responsive navigation at 390px, the three-step setup wizard, keyboard shortcuts, live status, and a persisted streamed chat on v10; v12 Chat also displayed the cold-cache RAG answer and citation. No page errors were observed. |
| PASS | API smoke covered health, models, model selection, conversation CRUD, memory CRUD/semantic retrieval, document upload/index/delete, settings, agent planning/cancellation/confirmation rejection, voice-auth status, and `/metrics`. |
| PASS | v12 ONEDIR contained no embedding or Whisper model weights. With an initially empty isolated Hugging Face cache, `all-MiniLM-L6-v2` downloaded on first RAG use (15 cache files, including 90,868,376-byte `model.safetensors`). |
| PASS | Frozen launcher defaults `HF_HOME` to `%LOCALAPPDATA%\\Aurora\\models\\huggingface`, a clear first-use cache path for embeddings and faster-whisper. Whisper model download and audio operation were not tested. |
| NOT TESTED | Hardware-dependent microphone capture, enrollment/verification, TTS playback, and the complete voice loop. |
| NOT TESTED | Live CI/staging/DevOps lifecycle, clean-machine VM, signing, updater/rollback, backup/restore, SmartScreen, disconnected offline operation, and outbound traffic capture. |
| BLOCKED | The existing unsigned ZIP still contains the v10 RAG behavior. No replacement candidate was packaged; do not treat it as a fixed or official release. |
| FAIL (resolved) | v8 RAG failed because Transformers could not find a runtime `transformers\models` directory. Dependency pinning alone exposed a second source-reload failure in v9; both were fixed and v10 RAG passed. |
| BLOCKED | Authorized external release-signing keys and an independently trusted fingerprint are unavailable. No official signature was created or verified. |
| BLOCKED | Clean Windows 10/11 VM execution and an authorized signed release remain prerequisites for official release and updater validation. The unsigned candidate must not be published as trusted or installed through the updater. |
| NOT TESTED | Clean Windows 10/11 VM without Python/developer tools. |
| NOT TESTED | Authenticode, update install, rollback, backup/restore, fully disconnected offline operation, voice/FFmpeg hardware, SmartScreen, or outbound traffic capture. |

## Phases 2–8 frozen app verification

**Target:** the existing v10 ONEDIR at `%TEMP%\\Aurora-release-build-v10-966f00120f3648a7ab8f4c1506544ab5\\portable-dist\\Aurora` was used for the Phase 2–8 UI and API matrix on `127.0.0.1:8000` with isolated user data. Playwright used Chromium against its frozen frontend. The grounding fix was then tested against local v12 ONEDIR, built from the same PyInstaller ONEDIR spec and existing production frontend, with a separate empty Hugging Face cache and isolated data. The existing v10 unsigned ZIP was not updated.

| Phase | Feature | Result | One-line evidence |
|---|---|---|---|
| 2 | Python 3.12 runtime / backend dependencies | PASS | Existing frozen v10 started and served health, model, database, and API routes without a developer Python runtime. |
| 2 | Default API/WebSocket port | PASS | Playwright chat connected to `/ws` on port 8000 and received a streamed assistant reply. |
| 2 | Offload blocking Ollama/TTS/STT/RAG work | NOT TESTED | No concurrent-load/event-loop measurement or hardware voice workload was run. |
| 2 | `.env` configuration | PASS | Fresh isolated launch created `config\\aurora.env`; health and active-model settings loaded. |
| 2 | Frontend `node_modules` installation | NOT TESTED | Frozen app served production assets; the build-time `node_modules` installation was not inspected. |
| 2 | Dark-mode default and light-theme toggle | PASS | Playwright loaded the dark UI and switched to light and back. |
| 2 | Live clock | PASS | Header displayed the current local date and time during Playwright checks. |
| 2 | Backend connection status indicator | PASS | Header and dashboard showed backend, Ollama, and database healthy while `/health` returned 200. |
| 2 | FFmpeg prerequisite documentation | PASS | `VOICE_SETUP.md` documents the optional FFmpeg path and direct PCM voice path. |
| 2 | Backend startup and WebSocket end-to-end | PASS | Frozen health was `ok`; chat WebSocket connected and returned an assistant message. |
| 2 | Backend API import | PASS | Frozen API initialized and served health, models, documents, memories, and settings routes. |
| 2 | Frontend production build | PASS | Frozen frontend loaded in Chromium with the expected title and all eight navigation entries; no fresh build was run. |
| 3 | `run.py` entry point / removal of legacy stub | NOT TESTED | The frozen desktop entry point ran; repository entry-point cleanup is not observable in the app. |
| 3 | Remove frontend `.bolt/` and backend lockfile | NOT TESTED | Repository cleanup cannot be verified through the frozen runtime. |
| 3 | Database schema and persistence | PASS | Isolated SQLite health passed; conversation and memory create/read/update/delete operations succeeded. |
| 3 | Core config, logging, and exception handling | PASS | Startup emitted structured JSON logs and an unconfirmed agent execution returned HTTP 400. |
| 3 | Service-interface boundaries | NOT TESTED | Public API operations worked, but internal module boundaries are not observable at runtime. |
| 3 | Structured JSON logging | PASS | Frozen startup and document-ingestion events were recorded as JSON in the isolated log. |
| 3 | `.env` and `.env.example` files | PASS | Packaged config template was copied on first launch and the API returned the configured local model. |
| 3 | Startup health checks | PASS | `/health` reported database `ok`, Ollama `true`, and model `llama3.2:3b`. |
| 4 | List installed models | PASS | `GET /api/models` returned the installed `llama3.2:3b` model. |
| 4 | Get/set active model | PASS | Active-model GET and PUT succeeded for the installed model; restart persistence was not separately checked. |
| 4 | Streaming `/ws` start/token/done flow | PASS | Browser chat completed over the frozen WebSocket and rendered the assistant reply. |
| 4 | Last-20-message context limit | NOT TESTED | Conversation persistence was checked, but a 20-message truncation boundary was not exercised. |
| 4 | Persist conversation messages | PASS | Streamed chat appeared in the History screen and conversation API. |
| 4 | Conversation REST create/read/update/delete | PASS | Temporary conversation CRUD completed successfully through frozen endpoints. |
| 4 | Chat screen | PASS | Playwright sent a message and observed the assistant response and document citation chip. |
| 4 | Conversation History screen | PASS | History screen loaded and displayed the persisted chat. |
| 4 | Model management screen | PASS | Models screen displayed the active installed model. |
| 4 | Header status/model/clock | PASS | Header showed healthy backend status, selected model, and local clock. |
| 5 | Memory schema and embeddings | PASS | Temporary memory create/update/delete completed with embedding generation; indexed document had one chunk. |
| 5 | Automatic memory extraction after each turn | NOT TESTED | Test conversations contained no durable user facts; extraction behavior was not verified. |
| 5 | Semantic memory retrieval | PASS | A temporary QA memory was retrieved in chat and the response returned its unique token. |
| 5 | Merge memory and document results | NOT TESTED | Memory and document retrieval were verified separately, not in a combined query. |
| 5 | Document upload and indexing | PASS | Cold-cache text upload returned `status=indexed` and one chunk. |
| 5 | Grounded RAG response | PASS | v10 and temperature-only v11 failed; v12 returned the retrieved fact and source citation on three cold-cache API queries and one Playwright Chat query. |
| 5 | Document listing | PASS | `GET /api/documents` returned the indexed test document. |
| 5 | Document deletion | PASS | DELETE removed the test record and its chunks; the list returned empty. |
| 5 | Chunk source/page/index metadata | PASS | Chat citation contained the test filename and `chunk_index: 0`; TXT correctly had no page number. |
| 5 | Knowledge Base screen | PASS | Playwright loaded the upload control and supported PDF/TXT/DOCX information. |
| 5 | Memory management screen | PASS | Playwright loaded the add/save controls and empty-memory state after cleanup. |
| 5 | Chat citations and persisted metadata | PASS | Chat rendered the source filename; API chat returned the matching source citation. |
| 6 | WebRTC VAD integration | NOT TESTED | No microphone/audio frames were captured; only the bundled Silero VAD asset was identified. |
| 6 | Fixed-frame VAD segmentation | NOT TESTED | No live audio input was supplied. |
| 6 | Speech-rate settings API | PASS | POST updated speech rate to 210 and GET returned 210. |
| 6 | Microphone selection behavior | NOT TESTED | Voice screen listed browser input devices, but no microphone was selected or used. |
| 6 | Interrupt/stop speech during playback | NOT TESTED | No audio playback was started. |
| 6 | Full voice → STT → LLM → TTS → playback loop | NOT TESTED | Hardware audio loop was intentionally not attempted. |
| 6 | Graceful missing-FFmpeg handling | NOT TESTED | No legacy encoded-audio input was submitted. |
| 6 | Voice settings panel | PASS | Playwright loaded Voice settings, microphone selector, speech-rate slider, and connected session status. |
| 7 | Voice enrollment feature | NOT TESTED | No microphone sample was recorded or enrolled. |
| 7 | Voice verification feature | NOT TESTED | No microphone sample/profile comparison was run. |
| 7 | Tool schemas, plan review, confirmation gate | PASS | Agent tools listed; generated plan awaited confirmation; `confirmed:false` was rejected with HTTP 400. |
| 7 | Allowlisted tool execution | NOT TESTED | Tool schemas were listed, but no desktop/clipboard action was executed. |
| 7 | Model-generated plan and five-step bound | PASS | A plan with one allowlisted step was created and persisted; a five-step boundary case was not generated. |
| 7 | Explicit confirmation required | PASS | Execute without confirmation returned HTTP 400 and the plan was then cancelled. |
| 7 | Plan/approval/history persistence and redaction | NOT TESTED | Cancelled plan persisted in history; executed-result redaction was not exercised. |
| 7 | Agent/task management screen | PASS | Playwright loaded plan form, optional voice-profile panel, and execution-history panel. |
| Pre-8 | Jira planning documentation and GitHub issue templates | NOT TESTED | No live Jira/GitHub account or planning workflow was exercised. |
| Pre-8 | Branching, PR review, protection, secrets, and tags | NOT TESTED | No live GitHub collaboration workflow was exercised. |
| Pre-8 | GitHub Actions workflows | NOT TESTED | CI workflows were not triggered as part of this app run. |
| Pre-8 | Jenkins gates, approval, and rollback | NOT TESTED | No live Jenkins/staging lifecycle was run. |
| Pre-8 | Backend/frontend containers and Compose profiles | NOT TESTED | Frozen ONEDIR was tested directly; Docker/Compose was not run. |
| Pre-8 | Pytest/Playwright/Java QA workflow integrations | NOT TESTED | Browser checks were manual Playwright; CI and Java QA workflows were not run. |
| Pre-8 | SonarQube/Jenkins scanner configuration | NOT TESTED | No live scanner or quality gate was run. |
| Pre-8 | Prometheus metrics endpoint | PASS | Frozen `GET /metrics` returned Prometheus-formatted counters. |
| Pre-8 | Staging checksums, deployment health, and rollback | NOT TESTED | No staging deployment or rollback lifecycle was run. |
| Pre-8 | Configure external accounts and credentials | NOT TESTED | Jira/GitHub/Jenkins/SonarQube credentials were not configured or exercised. |
| Pre-8 | Native Windows installer / clean-system validation | NOT TESTED | Installer and clean Windows VM were outside this frozen-app test. |
| 8 | Dark theme and light toggle | PASS | Both themes switched successfully in Playwright. |
| 8 | Responsive navigation across eight screens | PASS | All eight screens loaded; navigation and main area remained visible at 390px width. |
| 8 | Framer Motion page/setup transitions | PASS | Screen transitions and all three first-run wizard steps completed. |
| 8 | Live health/model/browser-heap status | PASS | Dashboard showed live service/database/model status and exposed browser heap estimate. |
| 8 | First-run username/model/voice steps | PASS | Wizard displayed name, installed-model selection, and optional voice-profile steps; no recording was attempted. |
| 8 | Dashboard sample data replacement | PASS | Dashboard showed current Ollama, database, model, and system-check state rather than samples. |
| 8 | Shared shell focus/scrollbar/reduced-motion polish | NOT TESTED | Responsive layout passed; focus, scrollbar, and reduced-motion behavior were not individually checked. |
| 8 | Keyboard shortcuts | PASS | Ctrl+N, Alt+4, `?`, and Escape changed screens/opened/dismissed the help dialog. |
| 8 | Error boundary recovery | NOT TESTED | No rendering error was injected to trigger the boundary. |

## Errors found and fixes

1. **Transformers 4.57 filesystem discovery (v8):** the installed version dynamically walked `transformers\models`, but PyInstaller keeps compiled modules in PYZ and the release excludes `.py` sources. Pinning `transformers==4.44.2` avoids that dynamic package scan; offline development embedding load passed.
2. **Transformers source reload (v9):** `transformers.processing_utils` called `direct_transformers_import()` to reopen `runtime\transformers\__init__.py`, which is intentionally not shipped as source. `desktop_launcher.py` now redirects only that exact frozen Transformers package-root reload to the already loaded package. `aurora.spec` explicitly forces Transformers modules into PYZ, and a focused regression test covers the fallback. The expanded frozen self-check and v10 RAG smoke passed.
3. **Torch config introspection:** the previous frozen workaround accepted `.config` but missed `._config`. The launcher now handles only source-less `torch.*.config` and `torch.*._config` module objects. Focused launcher tests passed.
4. **No OpenMP override:** `KMP_DUPLICATE_LIB_OK` is absent from the launcher and was not used. Frozen FAISS + Torch embedding completed successfully in v10 without an OpenMP duplicate-runtime crash.
5. **pytest asyncio configuration:** `backend/requirements-dev.txt` pins `pytest-asyncio==0.24.0`, which supports `asyncio_mode` and `asyncio_default_fixture_loop_scope`. The full suite reported no unknown-option warnings.
6. **RAG grounding (v10/v11, 2026-11-28):** cold-cache embedding, indexing, and source citation succeeded, but v10 at temperature `0.7` repeatedly ignored the relevant excerpt. An intermediate temperature-only v11 build also failed repeat testing, so it was not treated as a fix. `IntentRouter` now explicitly tells the model to treat retrieved excerpts as reference data, answer directly when relevant, and not claim present information is unavailable; configured generation temperature remains unchanged. The focused router suite passed (10 tests). A rebuilt v12 ONEDIR returned the fact plus citation on three API attempts and in a Playwright chat. The pre-existing v10 unsigned ZIP was not repackaged and retains the old behavior.

## Commands run and evidence

### RAG grounding regression and v12 ONEDIR rebuild

The v10 candidate's embedding model loaded from an empty isolated cache and indexed/cited a one-chunk document, but Ollama repeatedly ignored the retrieved fact. An intermediate v11 build changed only the contextual temperature to `0.0`; its cold-cache test still failed, so that change was removed. The final fix adds explicit grounding directions in the contextual prompt and preserves the configured temperature.

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest 'backend\tests\unit\test_intent_router.py' -q
```

Result: **10 passed in 2.65s**. The regression asserts the generated context prompt treats excerpts as reference data and directs the model to answer from relevant content.

The application was rebuilt as PyInstaller ONEDIR only; the existing production frontend was copied without rebuilding it:

```powershell
$buildRoot = Join-Path $env:TEMP 'Aurora-release-build-v12-rag-prompt-20261128'
& '.\backend\.venv\Scripts\python.exe' -m PyInstaller --noconfirm --clean `
  --distpath (Join-Path $buildRoot 'portable-dist') `
  --workpath (Join-Path $buildRoot 'portable-build') `
  '.\packaging\portable\aurora.spec'
New-Item -ItemType Directory -Force `
  (Join-Path $buildRoot 'portable-dist\Aurora\frontend\dist') | Out-Null
Copy-Item '.\frontend\dist\*' `
  (Join-Path $buildRoot 'portable-dist\Aurora\frontend\dist') -Recurse -Force
```

Result: **exit 0** with Python 3.12.10 / PyInstaller 6.22.3; v12 executable size **77,401,307 bytes**, frontend entry point present, and frozen `--self-check` passed. No frontend build, packaging script, signing action, or dirty-gate change was made.

With `HF_HOME`, `HF_HUB_CACHE`, and `TRANSFORMERS_CACHE` directed to a fresh isolated directory, the cache started with **0 files**. Document upload indexed the test text and downloaded `all-MiniLM-L6-v2`; the cache then held **15 files**, including `model.safetensors` (**90,868,376 bytes**). Three `POST /api/chat` requests each returned “The capital city of Noveria is Luminara.” and the `cold-cache-rag-v12.txt` source citation. Playwright sent the same question to the frozen v12 Chat screen and displayed the answer with that citation.

The existing v10 unsigned ZIP was neither modified nor repackaged. `package_portable.ps1` was not run for v12, the dirty-checkout gate was not disabled or bypassed, and no signing action was performed.

### Frozen application and model-cache checks

The v10 ONEDIR was run with an isolated data directory and `--port 8000 --no-browser`; `/health` returned database `ok`, Ollama `true`, and model `llama3.2:3b`. Playwright exercised the eight screens and interactive flows recorded in the verification matrix above. API smoke operations used temporary conversations, memories, documents, and agent plans. The final v12 ONEDIR was separately tested for cold-cache embedding download, document indexing, grounded API responses/citations, and the frozen Chat UI response/citation.

The v12 ONEDIR contained no embedding or Whisper model weights; the runtime includes the Silero VAD asset only. Its isolated Hugging Face cache began with **0 files** and, after RAG upload, contained **15 files**, including the `all-MiniLM-L6-v2` weight file of **90,868,376 bytes**. By default the launcher sets `HF_HOME` to `<Aurora user data>\models\huggingface` (normally `%LOCALAPPDATA%\Aurora\models\huggingface`); this is the clear first-use cache path for embeddings and faster-whisper. Whisper defaults to the `tiny` model and will download on first voice use; that download and audio operation were not attempted because no hardware voice test was in scope.

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

Result: **exit 0**. The raw ONEDIR health version was `0.3.0`; the extracted candidate contains `VERSION=1.0.0`, verified during the fresh extraction audit.

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

The local `backend\data\aurora.db` passed SQLite `PRAGMA quick_check` (`ok`) and contains 5 conversations, 4 messages, 1 memory, 2 settings, and 0 documents. Commit `49c3be3` removes it from the current tracked tree; the local database file was retained. It exists in Git history; deleting the current tracked copy does not purge prior commits. No history rewrite was performed.

## Packaging, signing, and Git status

`package_portable.ps1` checks `git status --porcelain --untracked-files=all` and refuses to proceed before creating output if the checkout is dirty. This gate was not disabled. An unsigned-candidate attempt returned:

```text
DIRTY_GATE_REJECTION=Commit all intended source changes and resolve unrelated changes before packaging.
OUTPUT_ROOT_CREATED=False
AURORA_RELEASE_PRIVATE_KEY=UNSET
AURORA_RELEASE_PUBLIC_KEY=UNSET
AURORA_RELEASE_KEY_FINGERPRINT=UNSET
```

The dirty-checkout gate was tested before the final commits and rejected packaging without creating an output root. After the intended changes were committed, packaging succeeded without disabling or bypassing that gate. The v10 ONEDIR build was then packaged as an explicitly unsigned engineering candidate. Do not describe it as signed or trusted.

The unsigned-candidate command was run only after a clean commit:

```powershell
$buildRoot = Join-Path $env:TEMP 'Aurora-release-build-v10-966f00120f3648a7ab8f4c1506544ab5'
$candidateRoot = Join-Path $env:TEMP ('Aurora-UNSIGNED-RC-' + [guid]::NewGuid().ToString('N'))
.\packaging\portable\package_portable.ps1 `
  -UnsignedCandidate `
  -OutputRoot $candidateRoot `
  -DistributionPath (Join-Path $buildRoot 'portable-dist\Aurora') `
  -ToolsDirectory (Join-Path $buildRoot 'portable-tools')
```

Expected output name: `Aurora-v1.0.0-Windows-x64-Portable-UNSIGNED-RC.zip`.

The command was run after commits `49c3be3`, `496e22f`, `eb2164b`, and `1626f01` left the checkout clean. Output:

```text
Created unsigned RC %TEMP%\Aurora-UNSIGNED-RC-1d60a660e7c24215a4f5b4151c835bdb\Aurora-v1.0.0-Windows-x64-Portable-UNSIGNED-RC.zip.
ZIP_SIZE_BYTES=364775586
SHA256=38295fdc0e6f027c1bf8b16e3e3a67d0a21a3ca7b9a8432cc04ff06f2bc631b8
RELEASE_ID=v1.0.0-1626f0157295-UNSIGNED-RC
BUILD_TIMESTAMP_UTC=2026-11-27T18:11:58Z
ZIP_CRC=PASS
UNSIGNED_MANIFEST=PASS
ZIP_MEMBER_COUNT=10550
ZIP_ROOTS=Aurora
FORBIDDEN_MEMBER_COUNT=0
EXTRACTED_FILE_COUNT=10550
VERSION=1.0.0
REQUIRED_STRUCTURE=PASS
FORBIDDEN_EXTRACTED_FILE_COUNT=0
EXTRACTED_SELF_CHECK_EXIT=0
```

The archive was extracted to `%TEMP%\AuroraRCX-1202ec1e4b28492a90259594c0551e5a`; self-check used isolated data at `%TEMP%\AuroraRCData-49d386dde12f42768d482fad952e24c4`. The sidecar hash and independently recomputed SHA-256 matched. The ZIP is a local engineering artifact, not an official release.

No authorized release keys or independently trusted fingerprint were available. Do not run the signed packaging path, publish a release, or use an unsigned candidate with the updater.

## Clean-machine and remaining blockers

`Test-PortableRelease.ps1` was not run: it requires a signed ZIP, an independently obtained trusted fingerprint/public key, and a clean Windows 10/11 x64 VM. The available Windows 11 build host has Python and developer tools. Clean-VM startup, ZIP verification/tampering, updater installation, user confirmation, rollback, data backup/restore, offline disconnected operation, voice/FFmpeg hardware, SmartScreen behavior, and outbound traffic observation remain **NOT TESTED**.

The portable README explains that Ollama and models are not bundled, Ollama inference is local, first-use model downloads require network unless cached, and Linux/macOS require separate builds. Full offline operation on a clean machine with no cached models is not verified.

## Files changed and commit groups

- `49c3be3 Stop tracking local Aurora database`: removed `backend/data/aurora.db` from the tracked tree; the local database remains on disk.
- `496e22f Fix portable runtime and release tests`: `backend/app/api.py`, `backend/app/core/config.py`, `backend/app/core/runtime_paths.py`, `backend/app/intent/load_documents.py`, `backend/app/intent/rag_service.py`, `backend/desktop_launcher.py`, `backend/pytest.ini`, `backend/requirements-dev.txt`, `backend/requirements.txt`, and `backend/tests/unit/test_portable_launcher.py`, `backend/tests/unit/test_portable_runtime_paths.py`, `backend/tests/unit/test_release_security.py`.
- `eb2164b Add portable release workflow`: `.github/workflows/release.yml`, `Test-PortableRelease.ps1`, `packaging/README.md`, `packaging/portable/CHANGELOG.md`, `README.txt`, `VERSION`, `aurora.spec`, `build_release.ps1`, `generate_checksums.ps1`, `nuitka-project.py` (not active), `package_portable.ps1`, `release_security.py`, `requirements-packaging.txt`, `resources/LICENSE.txt`, `resources/aurora.env.example`, `scripts/Backup-AuroraData.ps1`, `Restore-AuroraData.ps1`, `Rollback-Aurora.ps1`, `Update-Aurora.ps1`, `Verify-Release.ps1`, `start_aurora.py`, `verify_release.ps1`, and `verify_release.py`.
- `1626f01 Document portable release validation and blockers`: `ARCHITECTURE.md`, `CHANGELOG.md`, `DEPLOYMENT_GUIDE.md`, `DEVELOPMENT_PROGRESS.md`, `DEVELOPMENT_ROADMAP.md`, `LEARNING_NOTES.md`, `PORTABLE_RELEASE_CHECKLIST.md`, `README.md`, `RELEASE_GUIDE.md`, `RELEASE_VALIDATION_REPORT.md`, `SECURITY.md`, and `TESTING_GUIDE.md`.

The candidate ZIP and temporary extraction/data directories are outside the repository and are not committed.
