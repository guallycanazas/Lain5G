#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: docker compose --env-file .env -f docker-compose.yml logs --no-color"
  exit 0
fi

latest_run="$(find "$repo_dir/runs" -mindepth 1 -maxdepth 1 -type d -name 'run-*' | sort | tail -n 1 || true)"
if [ -n "$latest_run" ]; then
  mkdir -p "$latest_run/logs"
  (cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml logs --no-color) | tee "$latest_run/logs/docker-compose.log"
else
  (cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml logs --no-color)
fi
