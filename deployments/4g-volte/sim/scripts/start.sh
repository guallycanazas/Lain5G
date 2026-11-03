#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../../.." && pwd)"
env_file="$scenario_dir/../common/.env"

if [ ! -f "$env_file" ]; then echo "Missing $env_file" >&2; exit 2; fi
mkdir -p "$repo_dir/runs"
while :; do
  run_id="run-$(date -u +%Y%m%d-%H%M%S)"
  run_dir="$repo_dir/runs/$run_id"
  if mkdir "$run_dir" 2>/dev/null; then
    break
  fi
  sleep 1
done
mkdir -p "$run_dir/logs"
git_commit="$(git -C "$repo_dir" rev-parse --short HEAD 2>/dev/null || true)"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "$run_dir/metadata.json" <<JSON
{"run_id":"$run_id","scenario":"4g-volte-sim","deployment_path":"deployments/4g-volte/sim","started_at":"$started_at","finished_at":"","status":"started","git_commit":"$git_commit","validated_claims":[]}
JSON
printf '{"checks":[]}
' > "$run_dir/validation.json"
printf '{"created_at":"%s","metrics":[]}
' "$started_at" > "$run_dir/metrics.json"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: docker compose --env-file ../common/.env -f docker-compose.yml up -d"
  echo "Created run metadata: runs/$run_id"
  exit 0
fi

(cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml up -d)
echo "Created run metadata: runs/$run_id"
