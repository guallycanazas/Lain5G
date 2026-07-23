#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 4G LTE X310 FPGA-check plan; no device, UHD, Docker, or file access was performed"
  exit 0
fi
log="${1:-/tmp/lain5g-fpga-check.log}"
if [ "$#" -eq 0 ]; then
  "$(dirname "${BASH_SOURCE[0]}")/uhd-check.sh" >"$log" 2>&1 || true
fi
[ -f "$log" ] || { echo "fpga_status=unknown"; exit 1; }
if grep -Eiq 'incompatible|compat number mismatch|Expected FPGA' "$log"; then echo "fpga_status=incompatible"; exit 1; fi
if grep -Eiq 'uhd_fpga_compatible PASS|FPGA Version|fpga:' "$log"; then echo "fpga_status=compatible"; else echo "fpga_status=unknown"; exit 1; fi
