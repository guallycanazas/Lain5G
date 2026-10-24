#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: stop NSA RF and the EPC/IMS started by this profile; preserve a shared 4G core"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
"$script_dir/emergency-stop.sh"
if [ -f "$scenario_dir/.nsa-core-owned" ]; then
  core_dir="$scenario_dir/../4g-volte/x310"
  if [ -n "$(cd "$core_dir" && docker compose --env-file ../common/.env -f docker-compose.yml ps --status running -q enb-x310 2>/dev/null)" ]; then
    echo "Preserving the shared EPC/IMS because the 4G X310 eNB is using it."
  else
    "$repo_dir/deployments/4g-volte/x310/scripts/stop.sh"
    echo "Stopped the EPC/IMS started by the 5G NSA profile."
  fi
  rm -f "$scenario_dir/.nsa-core-owned"
fi
