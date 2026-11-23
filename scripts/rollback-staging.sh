#!/usr/bin/env bash
set -euo pipefail

backend_image="${1:-}"
if [[ ! "$backend_image" =~ ^aurora-backend:[A-Za-z0-9._-]+$ ]]; then
  echo "Usage: $0 aurora-backend:<previous-tag>" >&2
  exit 2
fi

export AURORA_BACKEND_IMAGE="$backend_image"
docker compose -p aurora-staging -f docker-compose.yml -f docker-compose.staging.yml up -d --no-build --force-recreate aurora-backend
curl --fail --silent --show-error http://localhost:18000/health
printf '\nStaging backend restored to %s\n' "$backend_image"
