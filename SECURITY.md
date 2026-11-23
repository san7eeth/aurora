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
