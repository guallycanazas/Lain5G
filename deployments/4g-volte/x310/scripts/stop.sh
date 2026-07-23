#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 4G LTE X310 stop plan; no Docker, file, or marker action was performed"
  exit 0
fi
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rm -f "$scenario_dir/.rf-active"
(cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml --profile rf stop)
