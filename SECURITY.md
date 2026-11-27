# Security Practices and Limitations

## Secrets and local data

- Keep `.env`, tokens, private keys, databases, uploaded documents, voice recordings, and clipboard contents out of Git and issue/PR attachments.
- `.env.example` contains defaults only. Replace local development credentials before using optional services outside a disposable environment.
- Configure Jenkins/SonarQube credentials in the service credential store; do not place tokens in pipeline files or command output.
- Treat logs, test reports, release archives, and uploaded documents as potentially sensitive. Review artifacts before sharing them.

## Network exposure

Compose application, monitoring, and SonarQube ports bind to loopback by default. Do not expose Jenkins, Grafana, SonarQube, or Aurora directly to an untrusted network without authentication, TLS, and network controls. The local Jenkins Compose service mounts the Docker socket, which grants broad control over the host Docker engine; use it only on a trusted isolated development machine.

The Windows package binds only to `127.0.0.1`. Its database, uploaded documents, model cache, and logs are kept in the current user's `%LOCALAPPDATA%\Aurora`. Review logs before sharing them.

## Application boundaries

- Agent execution is restricted to an allowlist and requires explicit plan approval. Review each plan before execution.
- Clipboard read and app-launch tools can expose or affect local user data. Treat their results as sensitive.
- Voice matching is approximate and must not be used as authentication or authorization.
- Ollama is a host-managed dependency and its availability/model behavior is not guaranteed by the application containers.
- `/metrics` currently exposes basic in-memory counters and no user content; counters reset on backend restart.

## Reporting

Do not publish secrets or exploit details in public issues. For a suspected vulnerability, contact the project maintainer privately with affected version, reproduction steps, impact, and a safe disclosure timeline. No dedicated security response service-level agreement is currently established.

The backend pins `python-multipart` to a patched release. Review dependency updates against the GitHub Advisory Database before merging them.

## Portable release trust

Portable ZIP files must be verified before extraction or execution with the bundled Ed25519 verifier. It pins the SHA-256 fingerprint supplied independently through the official developer channel, verifies the signed canonical manifest, checks each payload SHA-256, and rejects unlisted ZIP files and unsafe paths. Never place private signing keys in the repository, package, logs, or user data. The package builder requires externally held key paths; an official signing key and trust fingerprint must be provisioned by the authorized maintainer. SHA-256 alone detects corruption but does not establish publisher identity. PyInstaller does not make Python source impossible to recover.

Updater downloads are restricted to the configured official GitHub release endpoint, are verified before extraction, require user confirmation, and back up application files. User data is outside the app directory. Clean Windows 10/11 VM signature-tamper, rollback, offline, and update-preservation checks remain release gates.
