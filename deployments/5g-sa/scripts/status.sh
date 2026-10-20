#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: docker compose --env-file $env_file -f docker-compose.yml ps"
  exit 0
fi

(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml ps)
