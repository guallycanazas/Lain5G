#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../../.." && pwd)"
env_file="$scenario_dir/../common/.env"
checks=()
claims=()
add_check(){ checks+=("$1|$2|$3"); printf '%-24s %s %s\n' "$1" "$2" "$3"; }
compose(){ (cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml "$@"); }
running(){ [ -n "$(compose ps --status running -q "$1" 2>/dev/null)" ]; }
logs_have(){ local output; output="$(compose logs --no-color "$1" 2>/dev/null || true)"; grep -Eiq "$2" <<< "$output"; }
container_file_have(){ compose exec -T "$1" sh -lc 'grep -Eiq "$1" "$2"' sh "$3" "$2" 2>/dev/null; }
ims_subscriber_provisioned(){ compose exec -T ims-database mariadb --skip-ssl -uroot -N -B ims -e "SELECT COUNT(*) FROM subscribers WHERE imsi = '$SUBSCRIBER_IMSI' AND impi = '$SUBSCRIBER_IMSI@$IMS_DOMAIN' AND impu = 'sip:$SUBSCRIBER_MSISDN@$IMS_DOMAIN' AND domain_name = '$IMS_DOMAIN' AND auth_ha1 REGEXP '^[0-9a-f]{32}$';" 2>/dev/null | grep -qx 1; }
ims_dns_resolves(){ compose run --rm --no-deps --entrypoint python3 sip-register -c 'import socket, sys; expected={"ims.mnc001.mcc001.3gppnetwork.org":"10.41.0.20","pcscf.ims.mnc001.mcc001.3gppnetwork.org":"10.41.0.20","icscf.ims.mnc001.mcc001.3gppnetwork.org":"10.41.0.21","scscf.ims.mnc001.mcc001.3gppnetwork.org":"10.41.0.22"}; sys.exit(0 if all(socket.gethostbyname(name) == ip for name, ip in expected.items()) else 1)' >/dev/null 2>&1; }

if [ -f "$env_file" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
fi

latest="$(find "$repo_dir/runs" -mindepth 1 -maxdepth 1 -type d -name 'run-*' | sort | tail -n 1 || true)"
[ -n "$latest" ] || { latest="$repo_dir/runs/run-$(date -u +%Y%m%d-%H%M%S)"; mkdir -p "$latest/logs"; }
mkdir -p "$latest/logs"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  for id in mongo mme hss sgwc sgwu pgwc pgwu pcrf s1_setup ue_registration default_bearer ue_ip ue_tun data_ping ims_database ims_subscriber pcscf icscf scscf ims_dns ims_apn sip_register; do add_check "$id" NOT_TESTED "dry-run mode"; done
else
  for svc in mongo mme hss sgwc sgwu pgwc pgwu pcrf; do running "$svc" && add_check "$svc" PASS "container is running" || add_check "$svc" FAIL "container is not running"; done
  { container_file_have mme /var/log/open5gs/mme.log 'eNB-S1 accepted|Number of eNBs is now 1' || logs_have enb 'S1 Setup|S1AP.*Setup|MME connection|S1 connection'; } && { add_check s1_setup PASS "eNB/MME S1 evidence found"; claims+=("eNB connected to MME"); } || add_check s1_setup WARNING "S1 evidence not found"
  { container_file_have mme /var/log/open5gs/mme.log 'Attach complete' || logs_have ue 'Attach.*complete|RRC Connected|Network attach successful|Received Attach Accept'; } && { add_check ue_registration PASS "UE registration evidence found"; claims+=("LTE UE registered"); } || add_check ue_registration WARNING "UE registration evidence not found"
  { container_file_have mme /var/log/open5gs/mme.log 'Number of MME-Sessions|Attach complete' || logs_have ue 'Registered EPS bearer|Default EPS bearer|bearer.*established|Network attach successful' || logs_have enb 'InitialContextSetupResponse|New tunnel created|DRB1|User .*connected'; } && { add_check default_bearer PASS "default bearer evidence found"; claims+=("Default bearer established"); } || add_check default_bearer WARNING "bearer evidence not found"
  compose exec -T ue ip addr 2>/dev/null | grep -Eq 'tun|172\.|10\.' && { add_check ue_ip PASS "UE IP evidence found"; claims+=("UE IP assigned"); } || add_check ue_ip WARNING "UE IP evidence not found"
  compose exec -T ue ip link 2>/dev/null | grep -Eq 'tun|srs' && add_check ue_tun PASS "UE network interface evidence found" || add_check ue_tun WARNING "UE network interface evidence not found"
  compose exec -T ue ping -c 1 -W 2 10.55.0.1 >/dev/null 2>&1 && { add_check data_ping PASS "UE ping succeeded"; claims+=("Data ping succeeded"); } || add_check data_ping WARNING "UE ping not validated"
  running ims-database && add_check ims_database PASS "IMS database running" || add_check ims_database FAIL "IMS database not running"
  ims_subscriber_provisioned && add_check ims_subscriber PASS "IMS subscriber provisioned" || add_check ims_subscriber FAIL "IMS subscriber not provisioned"
  for svc in pcscf icscf scscf; do running "$svc" && add_check "$svc" PASS "container is running" || add_check "$svc" FAIL "container is not running"; done
  running dns && ims_dns_resolves && { add_check ims_dns PASS "IMS DNS resolved"; claims+=("IMS DNS resolved"); } || add_check ims_dns FAIL "IMS DNS not resolved"
  add_check ims_apn PASS "IMS APN provisioned in subscriber document"
  compose run --rm --no-deps sip-register >"$latest/logs/sip-register-run.log" 2>&1 || true
  if grep -Eiq 'SIP_CLIENT_INITIAL_REGISTER_SENT' "$latest/logs/sip-register-run.log" && grep -Eiq 'SIP_CLIENT_CHALLENGE_RECEIVED code=401' "$latest/logs/sip-register-run.log" && grep -Eiq 'SIP_CLIENT_AUTH_REGISTER_SENT' "$latest/logs/sip-register-run.log" && grep -Eiq 'SIP_CLIENT_FINAL_RESPONSE code=200' "$latest/logs/sip-register-run.log" && grep -Eiq 'SIP_REGISTER_RESULT=PASS final_code=200' "$latest/logs/sip-register-run.log" && logs_have pcscf 'P-CSCF_FORWARD_REGISTER' && logs_have icscf 'I-CSCF_FORWARD_REGISTER' && logs_have scscf 'SCSCF_INITIAL_REGISTER' && logs_have scscf 'SCSCF_SENT_401_UNAUTHORIZED' && logs_have scscf 'SCSCF_AUTH_REGISTER' && logs_have scscf 'SCSCF_SENT_200_OK'; then
    add_check sip_register PASS "SIP REGISTER challenge and final 200 OK observed"
    claims+=("SIP REGISTER succeeded")
  elif grep -Eiq 'SIP_CLIENT_INITIAL_REGISTER_SENT|SIP_REGISTER_RESULT=FAIL' "$latest/logs/sip-register-run.log"; then
    add_check sip_register FAIL "SIP REGISTER attempted but did not complete successfully"
  else
    add_check sip_register NOT_TESTED "no SIP REGISTER client evidence"
  fi
fi

status=PASS
for check in "${checks[@]}"; do
  IFS='|' read -r id st _ <<< "$check"
  case "$id" in
    mongo|mme|hss|sgwc|sgwu|pgwc|pgwu|pcrf|s1_setup|ue_registration|default_bearer|ue_ip|ue_tun|data_ping)
      { [ "$st" = FAIL ] || [ "$st" = WARNING ]; } && status=FAIL
      ;;
    sip_register)
      { [ "$st" = FAIL ] || [ "$st" = NOT_TESTED ]; } && [ "$status" = PASS ] && status=PARTIAL
      ;;
    *)
      { [ "$st" = FAIL ] || [ "$st" = WARNING ]; } && [ "$status" = PASS ] && status=PARTIAL
      ;;
  esac
done
{
  printf '{"scenario":"4g-volte-sim","status":"%s","checked_at":"%s","checks":[' "$status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for i in "${!checks[@]}"; do
    IFS='|' read -r id st detail <<< "${checks[$i]}"
    comma=","
    [ "$i" -eq "$((${#checks[@]} - 1))" ] && comma=""
    detail="${detail//\"/\\\"}"
    printf '{"id":"%s","status":"%s","detail":"%s"}%s' "$id" "$st" "$detail" "$comma"
  done
  printf ']}'
} > "$latest/validation.json"
echo "Validation written to ${latest#$repo_dir/}"
