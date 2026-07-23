#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G NSA X310 emergency-stop plan; no Docker, file, or marker action was performed"
  exit 0
fi
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
rm -f "$scenario_dir/.rf-active"
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf stop enb-nsa-x310 || true)
mkdir -p "$repo_dir/runs" 2>/dev/null || true
stopped_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
audit_file="$repo_dir/runs/5g-nsa-x310-emergency-stop-$(date -u +%Y%m%d-%H%M%S).json"
if ! printf '{"stopped_at":"%s","reason":"experimental NSA emergency stop"}\n' "$stopped_at" >"$audit_file"; then
  echo "WARNING: RF stopped, but the emergency-stop audit record could not be written" >&2
fi
