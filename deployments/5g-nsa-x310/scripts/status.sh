#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose ps"; exit 0; fi
(cd "$scenario_dir/../4g-volte/x310" && docker compose --env-file ../common/.env -f docker-compose.yml ps --format json)
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf ps --format json)
