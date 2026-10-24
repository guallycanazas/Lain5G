#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G NSA X310 validation plan; no RF, hardware, UHD, Docker, configuration, or file action was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"
mkdir -p "$run_dir/logs"
checks=()
add(){ checks+=("$1|$2|$3"); printf '%-26s %s %s\n' "$1" "$2" "$3"; }
json_escape(){ local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '%s' "$s"; }
core_compose(){ (cd "$scenario_dir/../4g-volte/x310" && docker compose --env-file ../common/.env -f docker-compose.yml "$@"); }
nsa_compose(){ (cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf "$@"); }
core_running(){ [ -n "$(core_compose ps --status running -q "$1" 2>/dev/null)" ]; }
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
"$script_dir/hardware-check.sh" >"$run_dir/logs/hardware-check.log" 2>&1 || true
if grep -q '^status=PASS$' "$run_dir/logs/hardware-check.log"; then
  add hardware_detected PASS "X-Series USRP found by UHD"
else
  add hardware_detected FAIL "X-Series USRP or UHD check failed; inspect hardware-check.log"
fi
grep -q '^dual_radio PASS' "$run_dir/logs/hardware-check.log" && add dual_rf_chains PASS "two RF chains and daughterboards detected" || add dual_rf_chains FAIL "two RF chains were not confirmed"

epc_failed=0
for service in mme hss sgwc sgwu pgwc pgwu pcrf; do core_running "$service" || epc_failed=1; done
[ "$epc_failed" -eq 0 ] && add epc_services PASS "shared LTE EPC services are running" || add epc_services FAIL "shared LTE EPC is incomplete"
ims_failed=0
for service in ims-database pcscf icscf scscf dns; do core_running "$service" || ims_failed=1; done
[ "$ims_failed" -eq 0 ] && add ims_services PASS "compact IMS services are running" || add ims_services FAIL "compact IMS services are incomplete"

if "$script_dir/preflight.sh" >"$run_dir/logs/preflight.log" 2>&1; then
  add rf_preflight PASS "non-transmitting NSA preflight passed"
else
  add rf_preflight FAIL "NSA preflight failed; inspect preflight.log"
fi

session_file=""
while IFS= read -r candidate; do
  if grep -q '"scenario":"5g-nsa-x310"' "$candidate"; then session_file="$candidate"; break; fi
done < <(find "$repo_dir/runs" -mindepth 2 -maxdepth 2 -type f -name rf-session.json -printf '%T@ %p\n' 2>/dev/null | sort -nr | cut -d' ' -f2-)
if [ -n "$session_file" ]; then
  session_status="$(sed -n 's/.*"status":"\([^"]*\)".*/\1/p' "$session_file" | head -n1)"
  session_id="$(sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p' "$session_file" | head -n1)"
  session_started="$(sed -n 's/.*"started_at":"\([^"]*\)".*/\1/p' "$session_file" | head -n1)"
  session_finished="$(sed -n 's/.*"finished_at":"\([^"]*\)".*/\1/p' "$session_file" | head -n1)"
  session_log="$(dirname "$session_file")/logs/enb-nsa-x310.log"
  mme_log="$(dirname "$session_file")/logs/mme.log"
  mme_container="$(core_compose ps -q mme 2>/dev/null || true)"
  if [ -n "$mme_container" ] && [ -n "$session_started" ]; then
    if [ -n "$session_finished" ]; then
      docker logs --timestamps --since "$session_started" --until "$session_finished" "$mme_container" >"$mme_log" 2>&1 || true
    else
      docker logs --timestamps --since "$session_started" "$mme_container" >"$mme_log" 2>&1 || true
    fi
  fi
  case "$session_status" in
    running|starting) add enb_started PASS "NSA eNB session $session_id is active"; add auto_stop NOT_TESTED "session is active; auto-stop is not yet observable";;
    auto_stopped) add enb_started PASS "NSA eNB ran for its guarded session ($session_id)"; add auto_stop PASS "container timeout completed ($session_id)";;
    stopped) add enb_started PASS "NSA eNB session was stopped by the operator ($session_id)"; add auto_stop NOT_TESTED "operator stop ended the session before auto-stop";;
    failed) add enb_started FAIL "NSA eNB failed during session $session_id"; add auto_stop FAIL "eNB exited before auto-stop ($session_id)";;
    *) add enb_started NOT_TESTED "latest NSA RF session state is unknown"; add auto_stop NOT_TESTED "latest NSA RF session state is unknown";;
  esac
  if [ -s "$session_log" ]; then
    if grep -Eiq 'RFNOC::GRAPH|RfnocError|RFNoC protocol mismatch|Failure to create rfnoc_graph|uhd_init failed|Management operation failed|Incorrect number of operations' "$session_log"; then
      add rfnoc_initialization FAIL "UHD could not initialize the RFNoC graph; inspect FPGA/UHD compatibility and the X310 management link ($session_id)"
    elif grep -Eiq '==== eNodeB started ====' "$session_log"; then
      add rfnoc_initialization PASS "eNB reached its started state after opening the UHD radio ($session_id)"
    else
      add rfnoc_initialization NOT_TESTED "captured log does not establish whether RFNoC initialization completed ($session_id)"
    fi
    if grep -Eiq 'S1 Setup|S1AP.*Setup|MME connection|Connected to MME' "$session_log" || grep -Eiq 'eNB-S1 accepted|Number of eNBs is now 1' "$mme_log" 2>/dev/null; then
      add s1_setup PASS "MME accepted the LTE eNB S1 control association in $session_id"
    else
      add s1_setup FAIL "LTE eNB S1 control association was not found in session-scoped eNB/MME logs ($session_id)"
    fi
    # RRC configuration lines such as "Cell idx=0" are emitted before UHD
    # opens the radio. Only count the NR carrier after srsENB actually tunes
    # RF port 1; UE/SCG attachment remains a separate external-UE check.
    grep -Eiq 'Setting frequency: DL=[0-9.]+ Mhz, DL_SSB=.*for cc_idx=1 nof_prb=' "$session_log" && add nr_secondary_cell PASS "NR secondary carrier frequency was applied to RF port 1 ($session_id)" || add nr_secondary_cell NOT_TESTED "NR secondary carrier was not confirmed on RF port 1 in the captured session ($session_id)"
    add logs_captured PASS "session-scoped eNB logs saved ($session_id)"
  else
    add rfnoc_initialization NOT_TESTED "session-scoped eNB log is unavailable ($session_id)"
    add s1_setup NOT_TESTED "session-scoped eNB log is unavailable ($session_id)"
    add nr_secondary_cell NOT_TESTED "session-scoped eNB log is unavailable ($session_id)"
    add logs_captured FAIL "session log was not captured ($session_id)"
  fi
else
  add rfnoc_initialization NOT_TESTED "no NSA RF session has been recorded"
  add enb_started NOT_TESTED "no NSA RF session has been recorded"
  add s1_setup NOT_TESTED "no active-session logs to check for LTE S1 setup"
  add nr_secondary_cell NOT_TESTED "no active-session logs to check for NR secondary-cell setup"
  add auto_stop NOT_TESTED "no completed NSA RF session to check for auto-stop"
  add logs_captured NOT_TESTED "no NSA RF session logs are available"
fi
add ue_registration NOT_TESTED "no EN-DC UE is included in this profile; UE attach must be verified with an external supported UE"

overall=PASS
has_pass=0
has_fail=0
has_warning=0
has_not_tested=0
for check in "${checks[@]}"; do IFS='|' read -r _ state _ <<< "$check"; [ "$state" != FAIL ] || overall=FAIL; done
for check in "${checks[@]}"; do
  IFS='|' read -r _ state _ <<< "$check"
  case "$state" in
    PASS) has_pass=1 ;;
    FAIL) has_fail=1 ;;
    WARNING) has_warning=1 ;;
    NOT_TESTED) has_not_tested=1 ;;
  esac
done
if [ "$has_fail" -eq 1 ]; then
  overall=FAIL
elif [ "$has_not_tested" -eq 1 ] && [ "$has_pass" -eq 1 ]; then
  overall=PARTIAL
elif [ "$has_not_tested" -eq 1 ]; then
  overall=NOT_TESTED
elif [ "$has_warning" -eq 1 ]; then
  overall=WARNING
fi
checked_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '{"scenario":"5g-nsa-x310","run_id":"%s","started_at":"%s"}\n' "$run_id" "$checked_at" > "$run_dir/metadata.json"
{
  printf '{"scenario":"5g-nsa-x310","status":"%s","checked_at":"%s","checks":[' "$overall" "$checked_at"
  for i in "${!checks[@]}"; do
    IFS='|' read -r id state detail <<< "${checks[$i]}"
    comma=","; [ "$i" -eq "$((${#checks[@]} - 1))" ] && comma=""
    printf '{"id":"%s","status":"%s","detail":"%s"}%s' "$(json_escape "$id")" "$state" "$(json_escape "$detail")" "$comma"
  done
  printf ']}'
} > "$run_dir/validation.json"
echo "Validation written to ${run_dir#$repo_dir/}/validation.json"
[ "$overall" = PASS ]
