#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G SA X310 validation plan; no RF, hardware, UHD, Docker, configuration, file, or marker action was performed"
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"
mkdir -p "$run_dir/logs"
checks=()

add(){ checks+=("$1|$2|$3"); printf '%-28s %s %s\n' "$1" "$2" "$3"; }
json_escape(){ local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '%s' "$s"; }
compose(){ (cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf "$@"); }
running(){ [ -n "$(compose ps --status running -q "$1" 2>/dev/null)" ]; }
write_json(){
  local status="PASS"
  for check in "${checks[@]}"; do IFS='|' read -r _ state _ <<< "$check"; [ "$state" = FAIL ] && status="FAIL"; done
  printf '{"scenario":"5g-sa-x310","run_id":"%s","created_at":"%s","dry_run":false}\n' "$run_id" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$run_dir/metadata.json"
  {
    printf '{"scenario":"5g-sa-x310","status":"%s","checked_at":"%s","checks":[' "$status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    for index in "${!checks[@]}"; do
      IFS='|' read -r id state detail <<< "${checks[$index]}"
      comma=","; [ "$index" -eq "$((${#checks[@]} - 1))" ] && comma=""
      printf '{"id":"%s","status":"%s","detail":"%s"}%s' "$(json_escape "$id")" "$state" "$(json_escape "$detail")" "$comma"
    done
    printf ']}'
  } > "$run_dir/validation.json"
  echo "Validation written to ${run_dir#$repo_dir/}/validation.json"
  [ "$status" = PASS ]
}

"$script_dir/hardware-check.sh" "$env_file" >"$run_dir/logs/hardware-check.log" 2>&1 && {
  add hardware_detected PASS "Compatible X300/X310 hardware detected"
  add uhd_available PASS "UHD hardware probe passed"
} || {
  add hardware_detected FAIL "Compatible X300/X310 hardware was not detected"
  add uhd_available FAIL "UHD hardware probe failed"
}

for service in mongo nrf ausf udm udr pcf upf smf amf; do running "$service" || core_fail=1; done
[ "${core_fail:-0}" = 0 ] && add core_services PASS "5G core services running" || add core_services FAIL "5G core services incomplete"
running amf && add amf_ready PASS "AMF running" || add amf_ready FAIL "AMF not running"

for service in ims-database pcscf icscf scscf dns; do running "$service" || ims_fail=1; done
[ "${ims_fail:-0}" = 0 ] && add ims_services PASS "Compact IMS infrastructure services running" || add ims_services FAIL "Compact IMS infrastructure incomplete"
add ims_registration NOT_TESTED "No physical UE IMS registration was attempted"
add vonr_call NOT_TESTED "No VoNR call dialog was attempted"
add rtp_media NOT_TESTED "No RTP media path was exercised"

REQUIRE_RF_READY=true "$script_dir/preflight.sh" >"$run_dir/logs/preflight.log" 2>&1 && add rf_preflight PASS "RF preflight passed" || add rf_preflight FAIL "RF preflight failed; inspect preflight.log"
if running gnb-x310; then
  add gnb_started PASS "gnb-x310 is currently running"
  started_at="$(docker inspect -f '{{.State.StartedAt}}' lain5g-lab-5g-sa-x310-gnb 2>/dev/null || true)"
  if [ -n "$started_at" ]; then compose logs --no-color --since "$started_at" gnb-x310 >"$run_dir/logs/gnb-x310.log" 2>/dev/null || true; else compose logs --no-color gnb-x310 >"$run_dir/logs/gnb-x310.log" 2>/dev/null || true; fi
  grep -Eiq 'NG Setup|AMF connection|Connected to AMF' "$run_dir/logs/gnb-x310.log" && add ng_setup PASS "NG setup evidence found in the active session" || add ng_setup FAIL "NG setup evidence not found in the active session"
  add auto_stop NOT_TESTED "RF session is still active; auto-stop cannot be confirmed yet"
  [ -s "$run_dir/logs/gnb-x310.log" ] && add logs_captured PASS "Active-session logs captured" || add logs_captured FAIL "No active-session gNB logs"
else
  add gnb_started NOT_TESTED "No active RF session; gnb-x310 remains in guarded standby"
  add ng_setup NOT_TESTED "No active RF session from which to collect NG evidence"
  add auto_stop NOT_TESTED "No current RF session lifecycle to validate"
  add logs_captured NOT_TESTED "No active RF session logs were requested"
fi

write_json
