#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G NSA X310 preflight plan; no configuration, hardware, UHD, Docker, network, file, or marker action was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
manifest="$scenario_dir/rf/safety-manifest.yaml"
channel="$scenario_dir/rf/channel-plan.yaml"
require_rf="${REQUIRE_RF_READY:-false}"
status=PASS
add(){ printf '%-30s %s %s\n' "$1" "$2" "$3"; [ "$2" = FAIL ] && status=FAIL; return 0; }
field(){ sed -n "s/^$1:[[:space:]]*//p" "$2" 2>/dev/null | tr -d '"' | head -n1; }

for file in "$scenario_dir/docker-compose.yml" "$scenario_dir/ran/enb.conf" "$scenario_dir/ran/rr.conf" "$manifest" "$channel"; do
  [ -f "$file" ] || add files FAIL "missing ${file#$scenario_dir/}"
done
docker image inspect lain5g-lab/srsran4g-uhd:local >/dev/null 2>&1 && add image PASS "srsRAN 4G UHD image exists" || add image FAIL "srsRAN 4G UHD image missing"
docker compose --env-file "$env_file" -f "$scenario_dir/docker-compose.yml" --profile rf config --quiet && add compose PASS "Compose config valid" || add compose FAIL "Compose config invalid"
lte_earfcn="$(field lte_dl_earfcn "$channel")"
nr_arfcn="$(field nr_dl_arfcn "$channel")"
nr_band="$(field nr_band "$channel")"
grep -Eq "dl_earfcn[[:space:]]*=[[:space:]]*$lte_earfcn;" "$scenario_dir/ran/rr.conf" && grep -Eq "dl_arfcn[[:space:]]*=[[:space:]]*$nr_arfcn;" "$scenario_dir/ran/rr.conf" && grep -Eq "band[[:space:]]*=[[:space:]]*$nr_band;" "$scenario_dir/ran/rr.conf" && add dual_rat PASS "LTE EARFCN $lte_earfcn and NR n$nr_band ARFCN $nr_arfcn configured" || add dual_rat FAIL "RAN and channel plan do not match"
grep -q 'rf_port = 0' "$scenario_dir/ran/rr.conf" && grep -q 'rf_port = 1' "$scenario_dir/ran/rr.conf" && add rf_ports PASS "two RF ports configured" || add rf_ports FAIL "two RF ports required"
grep -q 'sampling_rate=11.52e6' "$scenario_dir/ran/enb.conf" && add scs_rate PASS "15 kHz NSA sample rate configured" || add scs_rate FAIL "NSA sample rate missing"

duration="$(field maximum_duration_seconds "$manifest")"
auth="$(field authorization_confirmed "$manifest")"
auto_stop="$(field auto_stop "$manifest")"
capture_logs="$(field capture_logs "$manifest")"
lab_mode="$(field lab_mode "$manifest")"
nr_rf_path="$(field nr_rf_path_connected "$manifest")"
frequencies="$(field authorized_lab_frequencies "$channel")"
[[ "$duration" =~ ^[0-9]+$ ]] && [ "$duration" -ge 1 ] && [ "$duration" -le 600 ] && add duration PASS "${duration}s" || add duration FAIL "duration must be 1..600 seconds"
[ "$auto_stop" = true ] && add auto_stop PASS "enabled" || add auto_stop FAIL "auto_stop must be true"
[ "$capture_logs" = true ] && add capture_logs PASS "enabled" || add capture_logs FAIL "capture_logs must be true"
case "$lab_mode" in cabled|shielded) add lab_mode PASS "$lab_mode";; *) add lab_mode FAIL "cabled or shielded required";; esac

if [ "$require_rf" = true ]; then
  [ "$auth" = true ] && add authorization PASS "confirmed" || add authorization FAIL "authorization_confirmed must be true"
  [ "$frequencies" = true ] && add frequencies PASS "all four frequencies authorized" || add frequencies FAIL "authorized_lab_frequencies must be true"
  [ "$nr_rf_path" = true ] && add nr_rf_path PASS "second RF path connected" || add nr_rf_path FAIL "connect and attenuate the NR rf_port=1 path"
  [ -n "$(field operator_note "$manifest")" ] && add operator_note PASS "present" || add operator_note FAIL "operator note required"
  [ ! -f "$scenario_dir/../4g-volte/x310/.rf-active" ] && [ ! -f "$scenario_dir/../5g-sa-x310/.rf-active" ] && add rf_exclusive PASS "no other RF marker active" || add rf_exclusive FAIL "another RF scenario is active"
  [ -n "$(docker ps -q --filter name=lain5g-lab-4g-lte-x310-mme)" ] && add core_ready PASS "LTE MME running" || add core_ready FAIL "LTE core must be running"
else
  [ "$auth" = true ] && add authorization WARNING "authorization set; execution guard still required" || add authorization PASS "RF remains blocked"
  [ "$nr_rf_path" = true ] && add nr_rf_path PASS "second RF path declared connected" || add nr_rf_path WARNING "NR rf_port=1 path is disconnected"
fi

"$script_dir/hardware-check.sh" >/tmp/lain5g-nsa-hardware-check.log 2>&1 && add hardware PASS "dual-chain hardware reported" || add hardware FAIL "dual-chain hardware check failed"

echo "status=$status"
[ "$status" = PASS ]
