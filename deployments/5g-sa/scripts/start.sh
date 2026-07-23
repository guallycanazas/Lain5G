#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
run_id="run-$(date -u +%Y%m%d-%H%M%S)"
run_dir="$repo_dir/runs/$run_id"

if [ ! -f "$scenario_dir/.env" ]; then
  echo "Missing $scenario_dir/.env. Create it with: cp deployments/5g-sa/.env.example deployments/5g-sa/.env" >&2
  exit 2
fi

set -a
source "$scenario_dir/.env"
set +a

if [ "${LAIN5G_DRY_RUN:-false}" != "true" ]; then
  if [ -z "${SUBSCRIBER_KEY:-}" ] || [ -z "${SUBSCRIBER_OPC:-}" ]; then
    echo "SUBSCRIBER_KEY and SUBSCRIBER_OPC must be set in deployments/5g-sa/.env before starting." >&2
    exit 2
  fi

  x310_project="lain5g-lab-5g-sa-x310"
  x310_network="lain5g-lab-5g-sa-x310-core"
  if [ -n "$(docker ps -aq --filter "label=com.docker.compose.project=$x310_project")" ] || docker network inspect "$x310_network" >/dev/null 2>&1; then
    echo "Switching from 5G SA X310 to 5G SA simulation..."
    "$repo_dir/deployments/5g-sa-x310/scripts/stop.sh"
    echo "5G SA X310 stopped; volumes and data were preserved."
  fi

  project_name="lain5g-lab-5g-sa"
  existing_containers="$(docker ps -aq --filter "label=com.docker.compose.project=$project_name")"
  running_containers="$(docker ps -q --filter "label=com.docker.compose.project=$project_name")"
  if [ -n "$existing_containers" ] && [ -z "$running_containers" ]; then
    (cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml down --remove-orphans)
    echo "Removed stopped 5G SA containers with stale network references."
  fi
fi

mkdir -p "$run_dir/logs"
git_commit="$(git -C "$repo_dir" rev-parse --short HEAD 2>/dev/null || true)"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "$run_dir/metadata.json" <<JSON
{
  "run_id": "$run_id",
  "scenario": "5g-sa",
  "deployment_path": "deployments/5g-sa",
  "started_at": "$started_at",
  "finished_at": "",
  "status": "started",
  "git_commit": "$git_commit",
  "validated_claims": []
}
JSON
printf '{\n  "checks": []\n}\n' > "$run_dir/validation.json"
printf '{\n  "created_at": "%s",\n  "metrics": []\n}\n' "$started_at" > "$run_dir/metrics.json"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: docker compose --env-file .env -f docker-compose.yml up -d"
  echo "Created run metadata: runs/$run_id"
  exit 0
fi

(cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml up -d)
echo "Created run metadata: runs/$run_id"
