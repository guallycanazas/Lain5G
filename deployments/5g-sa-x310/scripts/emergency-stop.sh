#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: emergency stop gnb-x310"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf stop gnb-x310 >/dev/null 2>&1 || true)
rm -f "$scenario_dir/.rf-active"
echo "5G X310 gNB emergency stop completed"
