#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"

if [ ! -f "$scenario_dir/.env" ] && [ "${LAIN5G_DRY_RUN:-false}" != "true" ]; then
  echo "Missing $scenario_dir/.env. Create it from deployments/5g-vonr/.env.example and set secrets locally." >&2
  exit 2
fi

if [ -f "$scenario_dir/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$scenario_dir/.env"
  set +a
fi

if [ "${LAIN5G_DRY_RUN:-false}" != "true" ]; then
  for name in SUBSCRIBER_KEY SUBSCRIBER_OPC IMS_AUTH_PASSWORD; do
    if [ -z "${!name:-}" ]; then
      echo "$name must be set in deployments/5g-vonr/.env before starting." >&2
      exit 2
    fi
  done
fi

mkdir -p "$run_dir/logs"
git_commit="$(git -C "$repo_dir" rev-parse --short HEAD 2>/dev/null || true)"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '{"run_id":"%s","scenario":"5g-vonr-sim","deployment_path":"deployments/5g-vonr","started_at":"%s","finished_at":"","status":"started","git_commit":"%s","validated_claims":[]}\n' "$run_id" "$started_at" "$git_commit" > "$run_dir/metadata.json"
printf '{"scenario":"5g-vonr-sim","status":"NOT_TESTED","checks":[]}\n' > "$run_dir/validation.json"
printf '{"created_at":"%s","metrics":[]}\n' "$started_at" > "$run_dir/metrics.json"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: docker compose --env-file .env -f docker-compose.yml up -d"
  echo "Created run metadata: runs/$run_id"
  exit 0
fi

(cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml up -d)
echo "Created run metadata: runs/$run_id"
