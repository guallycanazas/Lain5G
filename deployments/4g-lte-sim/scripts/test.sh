#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker compose --env-file "$scenario_dir/../4g-volte/common/.env" -f "$scenario_dir/docker-compose.yml" config --quiet
LAIN5G_DRY_RUN=true "$scenario_dir/scripts/start.sh" >/dev/null
LAIN5G_DRY_RUN=true "$scenario_dir/scripts/status.sh" >/dev/null
LAIN5G_DRY_RUN=true "$scenario_dir/scripts/validate.sh" >/dev/null
