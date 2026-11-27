# Learning Notes

This file records the intended lessons from the project; use [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md) for evidence of what was actually verified.

## Software delivery and DevOps track — 2026-11-23

- Jira planning can be practiced manually first; the repository intentionally has no Jira API integration or stored Jira token.
- GitHub PR templates and issue templates give acceptance criteria and verification a consistent place. Branch protection is a host-side configuration and is not enabled by repository files alone.
- CI must fail when a required check fails. Preserve reports so a failure can be diagnosed instead of masking it with a successful exit.
- Docker Compose can run the app, tests, and optional quality/monitoring services without introducing a database microservice; SQLite remains embedded.
- Ollama stays host-managed. Containers use the host gateway, while GPU availability remains environment-specific.
- A configured pipeline is not proof of a working release. The end-to-end lifecycle still needs a host with Docker, credentials, and service accounts.
- SonarQube/Jenkins, Playwright, and Java QA are separate learning tools; Playwright remains the primary browser smoke-check configuration.
- Metrics are intentionally small and local. In-memory counters are not a durable production monitoring system.
- Keep the browser app and native installer status distinct. Phase 10 now produces and locally verifies a PyInstaller executable and Inno Setup installer; clean-account, WebSocket/voice, and first-run model checks remain.

### Follow-up practice

Run the documented checks locally, configure test credentials only in local service stores, execute a staging deployment, inspect reports, then update the milestone record with observed results.

## Desktop packaging track — 2026-11-23

- PyInstaller can package this Python/React app without adding a second backend or a database service; FastAPI serves the built frontend in packaged mode.
- Writable state must stay outside the one-file executable's temporary extraction directory. The package redirects SQLite, uploads, RAG index, model cache, and logs to the user's AppData folder.
- Ollama and its language models remain host-managed; the package owns Aurora's local files only.
- Installer definition and executable build are verified locally; clean-account install/uninstall verification is a separate release gate.
# Portable packaging notes — 2026-11-23

PyInstaller ONEDIR keeps the executable and native runtime dependencies in a directory structure, so the executable must remain alongside `_internal`. Release authenticity requires both an Ed25519 signature over canonical manifest bytes and SHA-256 checks for every listed package file; checksum files by themselves do not establish trust. User data belongs outside the application directory so updates can replace application files without replacing databases or documents. This implementation must still be exercised on a clean Windows VM before release.
