#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G NSA X310 hardware-check plan; no device, network, UHD, Docker, or file access was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
probe_log=/tmp/lain5g-5g-x310-usrp-probe.log
"$script_dir/../../5g-sa-x310/scripts/hardware-check.sh" "$scenario_dir/.env"
grep -q 'Radio#1' "$probe_log" || { echo "dual_radio FAIL second RF chain not reported"; exit 1; }
[ "$(grep -Ec 'TX Dboard:' "$probe_log")" -ge 2 ] || { echo "dual_dboard FAIL two TX daughterboards required"; exit 1; }
echo "dual_radio PASS two RF chains and daughterboards reported"
