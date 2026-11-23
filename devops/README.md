# Aurora software delivery and DevOps learning track

This track connects Jira planning, Git/GitHub review, CI, automated QA, Docker, SonarQube, staging, release artifacts, and monitoring. Account-specific services are configured locally; credentials and Jira API integration are not stored in the repository.

## Jira: manual project workflow

Create a Jira Scrum project named **Aurora Assistant** with key `AUR`. Start with a two-week sprint and these issue types:

- **Epic:** a product area such as “Aurora Chat Module” or “Voice and Agent Workflow”.
- **Story:** a user outcome with acceptance criteria and a story-point estimate.
- **Task/Sub-task:** implementation and QA work linked to a story.
- **Bug:** reproducible defect with expected/actual results, environment, severity, and workaround.

Use the flow **Backlog → To Do → In Progress → In Review → Done**. During refinement, ensure stories have testable acceptance criteria and dependencies; estimate with Fibonacci points (1, 2, 3, 5, 8, 13). Plan to team capacity. During sprint review, demo completed stories and update Jira; in the retrospective, record process improvements. Link PRs to Jira keys and update issues after merge or when blocked.

GitHub issue templates mirror the Jira story, task, and bug fields. Keep Jira work manual until the core app and team process are stable; do not add API tokens or Jira API integration for this learning stage.

## Git and GitHub

- `main` is release-ready; `develop` is the integration/staging branch.
- Branch from `develop` using `feature/<name>` or `bugfix/<name>`.
- Push focused branches, open PRs, link Jira/GitHub issues, describe acceptance criteria and verification, and wait for required checks.
- Protect `main` and `develop`: require PR review and passing CI/security checks; disallow force-pushes. Squash-merge approved changes.
- Keep README and operations/architecture docs current. Use semantic version tags such as `v1.2.0` after staging validation.
- Do not commit `.env`, credentials, tokens, databases, voice recordings, clipboard data, or local artifacts. Gitleaks and dependency review add checks; investigate findings rather than bypassing them.

See [`../CONTRIBUTING.md`](../CONTRIBUTING.md), the [PR template](../.github/PULL_REQUEST_TEMPLATE.md), and [GitHub issue templates](../.github/ISSUE_TEMPLATE/).

## Docker Compose development

Copy `.env.example` to `.env`, then from the repository root:

```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f aurora-backend
docker compose stop
docker compose start
```

Backend and static frontend run in containers; SQLite and monitoring data use named volumes. Ollama remains host-managed and is reached at `host.docker.internal`. There is no database container because SQLite is embedded. `docker compose down` removes containers/network but preserves volumes; `docker compose down -v` also deletes local persistent data.

Run the local QA profiles:

```powershell
New-Item -ItemType Directory -Force test-results/e2e | Out-Null
docker compose --profile qa run --build --rm aurora-tests
docker compose --profile qa run --build --rm aurora-tests pytest tests/integration -v -m integration
docker compose --profile qa run --build --rm aurora-e2e
```

Playwright uses Chromium and checks the UI, health/settings endpoints, and allowlisted tool registry without needing an Ollama response. Backend tests isolate/mock model and retrieval services.

## GitHub Actions and Jenkins CI/CD

`.github/workflows/ci.yml` checks Python lint, Bandit, dependency advisories, backend unit/integration tests, frontend lint/build, Docker images, Playwright UI/API smoke checks, and Java API/BDD checks. `.github/workflows/pr-checks.yml` adds dependency review and secret scanning. Failures are not converted to success; reports are uploaded for diagnosis.

The root `Jenkinsfile` follows those checks and adds SonarQube, checksummed package artifacts, and a manual staging approval for `develop`. Start Jenkins locally with:

```powershell
docker compose -f docker-compose.jenkins.yml up --build -d
docker compose -f docker-compose.jenkins.yml logs -f jenkins
```

Complete the Jenkins setup wizard, create a Pipeline or Multibranch Pipeline for the GitHub repository, and configure a Secret Text credential with ID `sonarqube-token`. Start SonarQube with `docker compose --profile devtools up -d sonarqube`, create an Aurora project token, and add it to Jenkins Credentials. The pipeline expects SonarQube at `http://host.docker.internal:9000`.

The local Jenkins container mounts the Docker Engine socket so it can build images; that socket grants host-level Docker control. Run this learning stack only on a trusted, isolated development machine. Keep Jenkins authentication enabled and do not expose its ports to an untrusted network.

When a pipeline fails, inspect the first failed stage and its archived report, reproduce the command locally, fix it on the feature branch, and push again. Check health and sanitized logs for service/configuration failures; inspect Docker logs for container startup failures; let test failures block the merge; use rollback after an unhealthy staging deploy.

## SonarQube

Start the local server with `docker compose --profile devtools up -d sonarqube`, then open `http://localhost:9000`, complete initial setup, create the Aurora project and token, and save the token in Jenkins as `sonarqube-token`. The pipeline waits for the quality gate on `main` and `develop`; address bugs, vulnerabilities, duplication, and maintainability findings before release.

## Monitoring and logs

- `/health` reports database and Ollama state; a healthy HTTP endpoint can still report model service degradation.
- `/metrics` exposes in-memory request count, server error count, and total request handling time. Counters reset when the backend restarts.
- Backend logs are structured JSON in Compose by default. Inspect `docker compose logs --since 10m aurora-backend` and correlate timestamps with Jenkins build IDs.
- Start the provisioned Prometheus/Grafana dashboard with `docker compose --profile monitoring up -d`. Prometheus is at `http://localhost:9090`; Grafana is at `http://localhost:3000`. The development Grafana default is `admin` / `aurora-local-only`; set `GRAFANA_ADMIN_PASSWORD` in `.env` before startup.

## Staging, release, and rollback

Jenkins stages a validated `develop` build only after manual approval. Staging uses `http://localhost:18000` for the backend and `http://localhost:18080` for the frontend:

```powershell
$env:AURORA_BACKEND_IMAGE = 'aurora-backend:local'
$env:AURORA_FRONTEND_IMAGE = 'aurora-frontend:local'
docker compose -p aurora-staging -f docker-compose.yml -f docker-compose.staging.yml up --build -d
Invoke-RestMethod http://localhost:18000/health
```

After validating, tag the approved `main` commit and push the tag. The release workflow builds/publishes a Docker image archive, frontend distribution ZIP, manifest, and SHA256 checksums as a GitHub Release. Keep the prior backend image tag for rollback:

```powershell
./scripts/rollback-staging.ps1 -BackendImage aurora-backend:123
```

or on a Linux agent:

```bash
./scripts/rollback-staging.sh aurora-backend:123
```

Aurora is currently a browser-hosted React app plus a Python service; the release workflow does not claim to create a native Windows desktop installer. That packaging needs a desktop shell and is tracked in Phase 10. Ollama stays host-managed; the app containers do not assume GPU access.

## Separate Java QA learning module

`qa-java/` independently demonstrates Maven, TestNG, REST Assured, Cucumber BDD, Selenium, and Page Object Model. CI runs REST Assured and Cucumber against the isolated smoke backend. Selenium is available locally with Chrome or a configured Grid:

```powershell
$env:AURORA_URL = 'http://localhost:5173'
$env:BACKEND_URL = 'http://localhost:8000'
$env:SELENIUM_REMOTE_URL = 'http://localhost:4444/wd/hub' # optional Grid
mvn -f qa-java/pom.xml -Dtest=AuroraUITest test
```

Playwright remains the primary browser check in CI; this Java module is for QA learning and is separate from Aurora's Python runtime.
