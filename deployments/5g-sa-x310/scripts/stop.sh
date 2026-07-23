#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose --profile rf stop gnb-x310 && docker compose down --remove-orphans"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf stop gnb-x310 >/dev/null 2>&1 || true)
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml down --remove-orphans)
rm -f "$scenario_dir/.rf-active"
