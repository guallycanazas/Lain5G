#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 4G LTE X310 preflight plan; no configuration, hardware, UHD, Docker, network, file, or marker action was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../../.." && pwd)"
env_file="$scenario_dir/../common/.env"
manifest="$scenario_dir/rf/safety-manifest.yaml"
channel="$scenario_dir/rf/channel-plan.yaml"
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"
mkdir -p "$run_dir/logs"
checks=()
add(){ checks+=("$1|$2|$3"); printf '%-28s %s %s\n' "$1" "$2" "$3"; }
json_escape(){ local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '%s' "$s"; }
[ -f "$env_file" ] && add env PASS ".env present" || add env FAIL ".env missing"
docker image inspect lain5g-lab/srsran4g-uhd:local >/dev/null 2>&1 && add image PASS "srsRAN UHD image exists" || add image FAIL "srsRAN UHD image missing"
[ -f "$channel" ] && add channel_file PASS "channel plan present" || add channel_file FAIL "channel plan missing"
[ -f "$manifest" ] && add safety_manifest PASS "safety manifest present" || add safety_manifest FAIL "safety manifest missing"
if [ -f "$manifest" ]; then
  grep -Eq '^authorization_confirmed:[[:space:]]*true' "$manifest" && add authorization PASS "authorization confirmed" || add authorization FAIL "authorization not confirmed"
  grep -Eq '^auto_stop:[[:space:]]*true' "$manifest" && add auto_stop PASS "auto-stop enabled" || add auto_stop FAIL "auto-stop must be true"
  grep -Eq '^capture_logs:[[:space:]]*true' "$manifest" && add capture_logs PASS "log capture enabled" || add capture_logs FAIL "capture_logs must be true"
  duration="$(sed -n 's/^maximum_duration_seconds:[[:space:]]*//p' "$manifest" | head -n1)"
  [[ "$duration" =~ ^[0-9]+$ ]] && [ "$duration" -gt 0 ] && [ "$duration" -le 600 ] && add duration PASS "duration ${duration}s" || add duration FAIL "duration must be 1..600 seconds"
  note="$(sed -n 's/^operator_note:[[:space:]]*//p' "$manifest" | tr -d '"' | head -n1)"
  [ -n "$note" ] && add operator_note PASS "operator note present" || add operator_note FAIL "operator note required"
  mode="$(sed -n 's/^lab_mode:[[:space:]]*//p' "$manifest" | head -n1)"
  case "$mode" in cabled|shielded|authorized) add lab_mode PASS "$mode";; *) add lab_mode FAIL "invalid lab_mode";; esac
  attenuation="$(sed -n 's/^attenuation_db:[[:space:]]*//p' "$manifest" | head -n1)"
  if [ "$mode" = cabled ]; then [[ "$attenuation" =~ ^[0-9]+$ ]] && [ "$attenuation" -ge 60 ] && add attenuation PASS "${attenuation} dB" || add attenuation FAIL "cabled mode requires >=60 dB"; fi
fi
if [ -f "$channel" ]; then
  grep -Eq '^downlink_frequency_hz:[[:space:]]*[0-9]+' "$channel" && add channel_frequency PASS "frequency configured" || add channel_frequency FAIL "frequency not configured"
fi
"$script_dir/hardware-check.sh" >"$run_dir/logs/hardware-check.log" 2>&1 && add hardware PASS "hardware check passed" || add hardware FAIL "hardware check failed"
"$script_dir/uhd-check.sh" >"$run_dir/logs/uhd-check.log" 2>&1 && add uhd PASS "UHD check passed" || add uhd FAIL "UHD check failed"
"$script_dir/fpga-check.sh" "$run_dir/logs/uhd-check.log" >"$run_dir/logs/fpga-check.log" 2>&1 && add fpga PASS "FPGA compatible" || add fpga FAIL "FPGA unknown or incompatible"
mme_addr="$(sed -n 's/^[[:space:]]*mme_addr[[:space:]]*=[[:space:]]*//p' "$scenario_dir/ran/enb.conf" | head -n1)"
if [ "$mme_addr" = "172.22.0.9" ]; then
  if [ "$(docker inspect -f '{{.State.Running}}' lain5g-lab-ims-real-4g-mme-1 2>/dev/null || true)" = true ]; then add epc PASS "real IMS MME running"; elif [ "${REQUIRE_RF_READY:-false}" = true ]; then add epc FAIL "real IMS MME must be running before RF start"; else add epc WARNING "real IMS EPC not running yet"; fi
elif (cd "$scenario_dir" && [ -n "$(docker compose --env-file ../common/.env -f docker-compose.yml ps --status running -q mme 2>/dev/null)" ]); then
  add epc PASS "MME running"
elif [ "${REQUIRE_RF_READY:-false}" = true ]; then add epc FAIL "MME must be running before RF start"; else add epc WARNING "EPC not running yet"; fi
status=PASS; for c in "${checks[@]}"; do IFS='|' read -r _ st _ <<< "$c"; [ "$st" = FAIL ] && status=FAIL; done
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
} > "$run_dir/preflight.json"
echo "Preflight written to ${run_dir#$repo_dir/}/preflight.json"
[ "$status" = PASS ]
