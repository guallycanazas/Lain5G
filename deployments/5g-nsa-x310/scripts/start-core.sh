#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
core_dir="$scenario_dir/../4g-volte/x310"
if [ "${LAIN5G_DRY_RUN:-false}" != true ]; then
  if [ -z "$(cd "$core_dir" && docker compose --env-file ../common/.env -f docker-compose.yml ps --status running -q mme 2>/dev/null)" ]; then
    printf 'started_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$scenario_dir/.nsa-core-owned"
  else
    rm -f "$scenario_dir/.nsa-core-owned"
  fi
fi
exec "$script_dir/../../4g-volte/x310/scripts/start-epc.sh"
