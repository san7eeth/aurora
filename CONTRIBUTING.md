# Contributing to Aurora

Aurora uses short-lived feature branches and pull requests so changes are reviewed and continuously checked before they reach `main`.

## Branches

- `main` contains release-ready changes.
- `develop` is the integration branch used for staging.
- Create `feature/<short-name>` for a feature and `bugfix/<short-name>` for a defect.
- Branch from `develop`, keep branches focused, and merge through a pull request. Do not push directly to `main`.

## Pull requests

Link the related Jira story or GitHub issue, list acceptance criteria, describe verification, and include sanitized screenshots/logs when useful. CI must pass before review. Resolve conversations and squash-merge to keep the integration history readable.

## Local quality checks

```powershell
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
Push-Location backend
flake8 app --max-line-length=120 --count --statistics
pytest tests/unit -v
pytest tests/integration -v -m integration
Pop-Location

Push-Location frontend
npm ci
npm run lint
npm run build
Pop-Location
```

For containerized UI/API smoke checks, see [`devops/README.md`](devops/README.md).

## Secrets and local data

Never commit `.env`, credentials, tokens, personal voice recordings, clipboard contents, local databases, vector indexes, uploaded documents, test artifacts, or release packages. Use `.env.example` for non-secret names/defaults and Jenkins/GitHub secret stores for credentials. Review secret-scan results even when a value looks like a test fixture.

## Release tags

Use semantic version tags such as `v1.2.0` only after staging validation and release review. Tag the approved `main` commit; the release workflow publishes checksummed Docker images and frontend artifacts. Native Windows installer packaging is tracked in Phase 10 because Aurora does not yet have a desktop shell.
