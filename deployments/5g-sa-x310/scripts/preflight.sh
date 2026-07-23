#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G SA X310 preflight plan; no configuration, hardware, UHD, Docker, network, file, or marker action was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
env_file="$scenario_dir/.env"
env_example="$scenario_dir/.env.example"
manifest="$scenario_dir/rf/safety-manifest.yaml"
manifest_example="$scenario_dir/rf/safety-manifest.example.yaml"
channel="$scenario_dir/rf/channel-plan.yaml"
channel_example="$scenario_dir/rf/channel-plan.example.yaml"
image="${LAIN5G_SRSRANPROJECT_UHD_IMAGE:-lain5g-lab/srsranproject-uhd:local}"
require_rf="${REQUIRE_RF_READY:-false}"
status=PASS
checks=()

add(){ checks+=("$1|$2|$3"); printf '%-30s %s %s\n' "$1" "$2" "$3"; [ "$2" = FAIL ] && status=FAIL; return 0; }
get_env(){ local key="$1" default="${2:-}"; local value="${!key:-}"; if [ -z "$value" ] && [ -f "$env_file" ]; then value="$(sed -n "s/^${key}=//p" "$env_file" | tail -n1)"; fi; if [ -z "$value" ] && [ -f "$env_example" ]; then value="$(sed -n "s/^${key}=//p" "$env_example" | tail -n1)"; fi; printf '%s' "${value:-$default}"; }
field(){ local key="$1" file="$2"; sed -n "s/^${key}:[[:space:]]*//p" "$file" 2>/dev/null | tr -d '"' | head -n1; }

active_manifest="$manifest_example"; [ -f "$manifest" ] && active_manifest="$manifest"
active_channel="$channel_example"; [ -f "$channel" ] && active_channel="$channel"

[ -f "$env_file" ] && add env PASS ".env present" || add env WARNING ".env missing; using .env.example for preparation checks"
if docker image inspect "$image" >/dev/null 2>&1; then
  add image PASS "$image exists"
  docker run --rm "$image" sh -lc 'ldd "$(command -v gnb)" | grep -Fq libuhd' && add gnb_uhd_link PASS "gNB links UHD" || add gnb_uhd_link FAIL "gNB binary does not link libuhd"
else
  add image FAIL "$image missing"
  add gnb_uhd_link FAIL "image missing"
fi
compose_env="$env_example"; [ -f "$env_file" ] && compose_env="$env_file"
docker compose --env-file "$compose_env" -f "$scenario_dir/docker-compose.yml" config --quiet && add compose_config PASS "docker compose config valid" || add compose_config FAIL "docker compose config invalid"

if grep -q 'image: lain5g-lab/srsranproject-uhd:local' "$scenario_dir/docker-compose.yml" && grep -q 'profiles: \["rf"\]' "$scenario_dir/docker-compose.yml"; then add gnb_profile PASS "gNB is isolated behind rf profile"; else add gnb_profile FAIL "gNB rf profile missing"; fi
grep -q 'network_mode: host' "$scenario_dir/docker-compose.yml" && add x310_network PASS "gNB can reach X310 over host Ethernet" || add x310_network FAIL "host network not configured for gNB"
grep -q 'addr: ${AMF_ADDR}' "$scenario_dir/gnb/gnb_x310.yml" && add gnb_config_template PASS "gNB config is parameterized" || add gnb_config_template FAIL "gNB config template missing AMF parameter"

amf_addr="$(get_env AMF_ADDR 10.20.0.5)"
gnb_bind="$(get_env GNB_BIND_ADDR 0.0.0.0)"
n3_bind="$(get_env N3_BIND_ADDR 0.0.0.0)"
[ -n "$amf_addr" ] && add amf_mapping PASS "AMF address set to $amf_addr" || add amf_mapping FAIL "AMF_ADDR missing"
[ -n "$gnb_bind" ] && add gnb_bind PASS "gNB bind address set" || add gnb_bind FAIL "GNB_BIND_ADDR missing"
[ -n "$n3_bind" ] && add n3_bind PASS "N3 bind address set" || add n3_bind FAIL "N3_BIND_ADDR missing"

mcc="$(get_env MCC 001)"; mnc="$(get_env MNC 01)"; tac="$(get_env TAC 1)"; sst="$(get_env SST 1)"; sd="$(get_env SD 000001)"
grep -Eq "mcc:[[:space:]]*$mcc" "$scenario_dir/open5gs/amf.yaml" && grep -Eq "mnc:[[:space:]]*$mnc" "$scenario_dir/open5gs/amf.yaml" && add plmn PASS "PLMN ${mcc}${mnc} matches Open5GS" || add plmn FAIL "PLMN does not match Open5GS AMF"
grep -Eq "tac:[[:space:]]*$tac" "$scenario_dir/open5gs/amf.yaml" && add tac PASS "TAC $tac matches Open5GS" || add tac FAIL "TAC mismatch"
grep -Eq "sst:[[:space:]]*$sst" "$scenario_dir/open5gs/amf.yaml" && grep -Eq "sd:[[:space:]]*$sd" "$scenario_dir/open5gs/amf.yaml" && add slice PASS "S-NSSAI $sst/$sd matches Open5GS" || add slice FAIL "S-NSSAI mismatch"

duration="$(field maximum_duration_seconds "$active_manifest")"
auto_stop="$(field auto_stop "$active_manifest")"
auth="$(field authorization_confirmed "$active_manifest")"
capture_logs="$(field capture_logs "$active_manifest")"
note="$(field operator_note "$active_manifest")"
mode="$(field lab_mode "$active_manifest")"
attenuation="$(field attenuation_db "$active_manifest")"
[[ "$duration" =~ ^[0-9]+$ ]] && [ "$duration" -gt 0 ] && [ "$duration" -le 600 ] && add duration PASS "duration ${duration}s" || add duration FAIL "duration must be 1..600 seconds"
[ "$auto_stop" = true ] && add auto_stop PASS "auto-stop enabled" || add auto_stop FAIL "auto_stop must be true"
[ "$capture_logs" = true ] && add capture_logs PASS "log capture enabled" || add capture_logs FAIL "capture_logs must be true"
case "$mode" in cabled|shielded|authorized) add lab_mode PASS "$mode";; *) add lab_mode FAIL "invalid lab_mode";; esac
if [ "$mode" = cabled ]; then [[ "$attenuation" =~ ^[0-9]+$ ]] && [ "$attenuation" -ge 60 ] && add attenuation PASS "${attenuation} dB" || add attenuation FAIL "cabled mode requires >=60 dB"; fi

if [ "$require_rf" = true ]; then
  [ -f "$env_file" ] || add rf_env FAIL ".env required for RF-ready start"
  [ -f "$manifest" ] || add rf_manifest FAIL "safety-manifest.yaml required"
  [ -f "$channel" ] || add rf_channel FAIL "channel-plan.yaml required"
  [ "$auth" = true ] && add authorization PASS "authorization confirmed" || add authorization FAIL "authorization_confirmed must be true"
  [ -n "$note" ] && add operator_note PASS "operator note present" || add operator_note FAIL "operator_note required"
  (cd "$scenario_dir" && [ -n "$(docker compose --env-file "$env_file" -f docker-compose.yml ps --status running -q amf 2>/dev/null)" ]) && add core_ready PASS "AMF running" || add core_ready FAIL "AMF must be running before RF start"
else
  [ "$auth" = true ] && add authorization WARNING "authorization true in active manifest; RF still blocked unless start guard is set" || add authorization PASS "authorization not confirmed; RF start remains blocked"
fi

dl_arfcn="$(get_env DL_ARFCN "$(field dl_arfcn "$active_channel")")"
nr_band="$(get_env NR_BAND "$(field nr_band "$active_channel")")"
bandwidth="$(get_env CHANNEL_BANDWIDTH_MHZ 10)"
sample_rate="$(get_env SAMPLE_RATE_MHZ 15.36)"
tx_gain="$(get_env TX_GAIN)"
rx_gain="$(get_env RX_GAIN)"
case "$bandwidth:$sample_rate" in
  5:15.36|10:15.36|15:23.04|20:23.04|40:46.08|50:61.44|100:122.88) add sample_rate PASS "${bandwidth} MHz uses ${sample_rate} Msps" ;;
  *) add sample_rate FAIL "unsupported bandwidth/sample-rate pair: ${bandwidth} MHz / ${sample_rate} Msps" ;;
esac
if [ "$require_rf" = true ]; then
  [[ "$dl_arfcn" =~ ^[0-9]+$ ]] && add dl_arfcn PASS "DL_ARFCN set" || add dl_arfcn FAIL "DL_ARFCN required"
  [[ "$nr_band" =~ ^n?[0-9]+$ ]] && add nr_band PASS "NR band set" || add nr_band FAIL "NR_BAND required"
  [[ "$tx_gain" =~ ^[0-9]+([.][0-9]+)?$ ]] && add tx_gain PASS "TX gain set" || add tx_gain FAIL "TX_GAIN required"
  [[ "$rx_gain" =~ ^[0-9]+([.][0-9]+)?$ ]] && add rx_gain PASS "RX gain set" || add rx_gain FAIL "RX_GAIN required"
else
  [ -n "$dl_arfcn" ] && add dl_arfcn PASS "DL_ARFCN set" || add dl_arfcn NOT_TESTED "operator must set DL_ARFCN locally"
  [ -n "$nr_band" ] && add nr_band PASS "NR band set" || add nr_band NOT_TESTED "operator must set NR_BAND locally"
  [ -n "$tx_gain" ] && add tx_gain PASS "TX gain set" || add tx_gain NOT_TESTED "operator must set TX_GAIN locally"
  [ -n "$rx_gain" ] && add rx_gain PASS "RX gain set" || add rx_gain NOT_TESTED "operator must set RX_GAIN locally"
fi

"$script_dir/hardware-check.sh" >/tmp/lain5g-5g-x310-hardware-check.log 2>&1 && add hardware PASS "hardware check passed" || add hardware FAIL "hardware check failed"

printf 'status=%s\n' "$status"
[ "$status" = PASS ]
