# Changelog

## Unreleased — portable Windows distribution

- Added a PyInstaller ONEDIR portable ZIP workflow with a stable `Aurora/` root, separate runtime, `Start Aurora.exe`, launcher dependency diagnostics, and x64/Windows checks.
- Added a signed release manifest with semantic version, release ID, UTC build timestamp, notes, key fingerprint, and strict per-file SHA-256 verification.
- Added optional official-release/offline ZIP update, signed-notes confirmation, application backup/rollback, data export/restore, a Nuitka standalone project entry point, and [RELEASE_GUIDE.md](RELEASE_GUIDE.md).
- Added a LocalAppData directory layout and non-overwriting migration from the previous flat database/document/index paths.
- Added focused tests for signed manifest generation, invalid signatures, tampering, fingerprint mismatch, unsafe paths and archive layout.
- The clean Windows VM run, final ZIP build/signing, and publication remain pending. Nuitka is not the active release compiler; validate it before changing the established PyInstaller build.

User-facing and workflow changes are recorded here. Dates use Asia/Calcutta local time where a timestamp is needed. Verification status is kept in [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md).

## Unreleased — 2026-11-23

### Security

- Updated `python-multipart` from 0.0.9 to 0.0.34 to address the reported high-severity multipart parser advisories.

### Phase 10 packaging work

- Added same-origin frontend serving, per-user packaged data paths, Windows start/stop control, PyInstaller and Inno Setup definitions, an app icon, and build documentation.
- Built the 358 MB Windows executable and 355 MB Inno Setup installer; health/static/API, graceful shutdown, and temporary install/uninstall checks passed.
- Clean Windows account/VM, WebSocket/voice, and first-run model-download checks remain pending.

### Phase 9 testing work

- Added isolated test coverage for startup/service failures, Ollama HTTP behavior, streaming, persistence CRUD, voice profiles, STT/TTS, malformed files, and tool safety.
- Moved RAG's heavy model import to first use and bound the native backend default to loopback after CI lint/security checks exposed the issues.
- Synchronous test subset, compile, lint, and Bandit passed; async/API/WebSocket coverage remains unverified due sandbox socket restrictions.

### Phase 8 UI work

- Replaced dashboard mock metrics with live service/model status and browser heap reporting when available.
- Added first-run personalization, animated screen transitions, keyboard shortcuts, responsive shell refinements, and an error fallback.
- Frontend lint, TypeScript, and production build pass; interactive behavior remains unverified.

### Added

- DevOps learning workflow documentation, Jira-mirroring GitHub templates, CI/CD configuration, Docker Compose QA/staging profiles, monitoring configuration, release packaging, and rollback scripts.
- Project operations and learning documents: architecture, testing, deployment, security, learning notes, and this changelog.
- Clear milestone evidence requirements in the development progress record.

### Changed

- README now links the project architecture, testing, deployment, security, progress, and learning documentation.

### Verification status

- Repository configuration and selected frontend/backend checks are recorded in [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md). Automated suites, Java compilation, live CI, and deployment have not all been verified; do not treat configured workflows as successful execution.
