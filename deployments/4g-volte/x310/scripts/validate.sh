#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 4G LTE X310 validation plan; no RF, hardware, UHD, Docker, configuration, file, or marker action was performed"
  exit 0
fi
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../../.." && pwd)"
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"
mkdir -p "$run_dir/logs"
checks=()
add(){ checks+=("$1|$2|$3"); printf '%-26s %s %s\n' "$1" "$2" "$3"; }
json_escape(){ local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '%s' "$s"; }
compose(){ (cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml --profile rf "$@"); }
running(){ [ -n "$(compose ps --status running -q "$1" 2>/dev/null)" ]; }
write_json(){
  local status="PASS"
  for c in "${checks[@]}"; do IFS='|' read -r _ st _ <<< "$c"; [ "$st" = FAIL ] && status="FAIL"; done
  printf '{"scenario":"4g-lte-x310","run_id":"%s","created_at":"%s","dry_run":%s}\n' "$run_id" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$([ "${LAIN5G_DRY_RUN:-false}" = "true" ] && printf true || printf false)" > "$run_dir/metadata.json"
  {
    printf '{"scenario":"4g-lte-x310","status":"%s","checked_at":"%s","checks":[' "$status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    for i in "${!checks[@]}"; do
      IFS='|' read -r id st detail <<< "${checks[$i]}"
      comma=","
      [ "$i" -eq "$((${#checks[@]} - 1))" ] && comma=""
      printf '{"id":"%s","status":"%s","detail":"%s"}%s' "$(json_escape "$id")" "$st" "$(json_escape "$detail")" "$comma"
    done
    printf ']}'
  } > "$run_dir/validation.json"
  echo "Validation written to ${run_dir#$repo_dir/}/validation.json"
  [ "$status" = PASS ]
}
"$(dirname "${BASH_SOURCE[0]}")/hardware-check.sh" >"$run_dir/logs/hardware-check.log" 2>&1 && add hardware_detected PASS "X310 detected" || add hardware_detected FAIL "X310 not detected"
grep -q 'ethernet_link.*PASS' "$run_dir/logs/hardware-check.log" && add ethernet_link PASS "compatible local subnet found" || add ethernet_link WARNING "ethernet not proven compatible"
"$(dirname "${BASH_SOURCE[0]}")/uhd-check.sh" >"$run_dir/logs/uhd-check.log" 2>&1 && add uhd_available PASS "UHD probe passed" || add uhd_available FAIL "UHD probe failed"
"$(dirname "${BASH_SOURCE[0]}")/fpga-check.sh" "$run_dir/logs/uhd-check.log" >"$run_dir/logs/fpga-check.log" 2>&1 && add uhd_fpga_compatible PASS "FPGA compatible" || add uhd_fpga_compatible FAIL "FPGA compatibility unknown"
for svc in mme hss sgwc sgwu pgwc pgwu pcrf; do running "$svc" || epc_fail=1; done; [ "${epc_fail:-0}" = 0 ] && add epc_services PASS "EPC services running" || add epc_services FAIL "EPC incomplete"
running mme && add mme_ready PASS "MME running" || add mme_ready FAIL "MME not running"
for svc in pcscf icscf scscf; do running "$svc" || ims_fail=1; done; [ "${ims_fail:-0}" = 0 ] && add ims_services PASS "IMS services running" || add ims_services FAIL "IMS incomplete"
if [ -f "$scenario_dir/.rf-active" ]; then add enb_started WARNING "RF session marker still present"; else add enb_started PASS "RF session completed"; fi
compose logs --no-color enb-x310 >"$run_dir/logs/enb-x310.log" 2>/dev/null || true
grep -Eiq 'S1 Setup|S1AP|MME connection|Connected to MME' "$run_dir/logs/enb-x310.log" && add s1_setup PASS "S1 setup evidence found" || add s1_setup FAIL "S1 setup evidence not found"
compose ps enb-x310 2>/dev/null | grep -q running && add auto_stop FAIL "enb-x310 still running" || add auto_stop PASS "enb-x310 is stopped"
[ -s "$run_dir/logs/enb-x310.log" ] && add logs_captured PASS "logs captured" || add logs_captured FAIL "no enb-x310 logs"
add ue_registration NOT_TESTED "UE over RF not required in this profile"
write_json
