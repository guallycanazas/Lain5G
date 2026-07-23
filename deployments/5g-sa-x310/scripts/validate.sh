#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G SA X310 validation plan; no RF, hardware, UHD, Docker, configuration, file, or marker action was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
status=PASS
check(){ printf '%-28s %s %s\n' "$1" "$2" "$3"; [ "$2" = FAIL ] && status=FAIL; return 0; }

docker image inspect lain5g-lab/srsranproject-uhd:local >/dev/null 2>&1 && check image PASS "srsRAN Project UHD image exists" || check image FAIL "image missing"
docker run --rm lain5g-lab/srsranproject-uhd:local gnb --version >/tmp/lain5g-5g-x310-gnb-version.log 2>&1 && check gnb_binary PASS "gnb binary available" || check gnb_binary FAIL "gnb binary unavailable"
docker run --rm lain5g-lab/srsranproject-uhd:local sh -lc 'ldd "$(command -v gnb)" | grep -Fq libuhd' && check gnb_uhd_link PASS "gNB links UHD" || check gnb_uhd_link FAIL "gNB binary does not link libuhd"
docker run --rm lain5g-lab/srsranproject-uhd:local uhd_config_info --version 2>/dev/null | grep -Fq '4.10.0' && check uhd_version PASS "UHD 4.10 available" || check uhd_version FAIL "UHD 4.10 unavailable"
docker compose --env-file "$scenario_dir/.env.example" -f "$scenario_dir/docker-compose.yml" config --quiet && check compose_config PASS "Compose config valid" || check compose_config FAIL "Compose config invalid"
LAIN5G_DRY_RUN=true "$script_dir/preflight.sh" >/tmp/lain5g-5g-x310-preflight-dry-run.log 2>&1 && check preflight PASS "safe preflight passes in dry-run" || check preflight FAIL "preflight failed"
LAIN5G_DRY_RUN=true "$script_dir/start-gnb.sh" >/tmp/lain5g-5g-x310-rf-dry-run.log 2>&1 && check rf_dry_run PASS "RF dry-run path does not transmit" || check rf_dry_run FAIL "RF dry-run failed"
check actual_rf NOT_TESTED "RF transmission intentionally not executed"
check cots_ue NOT_TESTED "COTS UE registration intentionally not attempted"
echo "status=$status"
[ "$status" = PASS ]
