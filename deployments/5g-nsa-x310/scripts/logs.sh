#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose logs enb-nsa-x310"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf logs --no-color --tail "${LAIN5G_LOG_TAIL_LINES:-500}" enb-nsa-x310)
