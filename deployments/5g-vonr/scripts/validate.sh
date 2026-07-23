#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"
mkdir -p "$run_dir/logs"

checks=()
claims=()
metrics=()
add_check(){ checks+=("$1|$2|$3"); printf '%-30s %s %s\n' "$1" "$2" "$3"; }
add_claim(){ claims+=("$1"); }
add_metric(){ metrics+=("$1|$2"); }
json_escape(){ local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '%s' "$s"; }
compose(){ (cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml --profile sip "$@"); }
running(){ [ -n "$(compose ps --status running -q "$1" 2>/dev/null)" ]; }
logs_have(){ local output; output="$(compose logs --no-color "$1" 2>/dev/null || true)"; grep -Eiq "$2" <<< "$output"; }
exec_ok(){ local svc="$1"; shift; compose exec -T "$svc" "$@" >/tmp/lain5g-vonr-validate.$$ 2>&1; }
exec_out(){ local svc="$1"; shift; compose exec -T "$svc" "$@" 2>/dev/null; }

if [ -f "$scenario_dir/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$scenario_dir/.env"
  set +a
fi

write_outputs(){
  local status="PASS"
  if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
    status="NOT_TESTED"
  fi
  local critical="mongo nrf amf smf upf ausf udm udr pcf ng_setup ue_registration pdu_internet pdu_ims ue_internet_ip ue_ims_ip ue_internet_tun ue_ims_tun data_ping"
  if [ "${LAIN5G_DRY_RUN:-false}" != "true" ]; then
    for check in "${checks[@]}"; do
      IFS='|' read -r id st _ <<< "$check"
      if [[ " $critical " == *" $id "* ]] && { [ "$st" = FAIL ] || [ "$st" = WARNING ] || [ "$st" = NOT_TESTED ]; }; then
        status="FAIL"
      fi
    done
  fi
  if [ "$status" = PASS ]; then
    for check in "${checks[@]}"; do
      IFS='|' read -r id st _ <<< "$check"
      case "$id" in
        ims_database|pcscf|icscf|scscf|ims_dns|pcscf_reachable_over_ims)
          { [ "$st" = FAIL ] || [ "$st" = WARNING ] || [ "$st" = NOT_TESTED ]; } && status="PARTIAL"
          ;;
        sip_register)
          { [ "$st" = FAIL ] || [ "$st" = NOT_TESTED ] || [ "$st" = WARNING ]; } && status="PARTIAL"
          ;;
      esac
    done
  fi
  local now git_commit
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git_commit="$(git -C "$repo_dir" rev-parse --short HEAD 2>/dev/null || true)"
  {
    printf '{"run_id":"%s","scenario":"5g-vonr-sim","deployment_path":"deployments/5g-vonr","started_at":"%s","finished_at":"%s","status":"%s","git_commit":"%s","validated_claims":[' "$run_id" "$now" "$now" "$status" "$git_commit"
    for i in "${!claims[@]}"; do
      comma=","; [ "$i" -eq "$((${#claims[@]} - 1))" ] && comma=""
      printf '"%s"%s' "$(json_escape "${claims[$i]}")" "$comma"
    done
    printf ']}'
  } > "$run_dir/metadata.json"
  {
    printf '{"scenario":"5g-vonr-sim","status":"%s","checked_at":"%s","checks":[' "$status" "$now"
    for i in "${!checks[@]}"; do
      IFS='|' read -r id st detail <<< "${checks[$i]}"
      comma=","; [ "$i" -eq "$((${#checks[@]} - 1))" ] && comma=""
      printf '{"id":"%s","status":"%s","detail":"%s"}%s' "$(json_escape "$id")" "$st" "$(json_escape "$detail")" "$comma"
    done
    printf ']}'
  } > "$run_dir/validation.json"
  {
    printf '{"created_at":"%s","metrics":[' "$now"
    for i in "${!metrics[@]}"; do
      IFS='|' read -r id value <<< "${metrics[$i]}"
      comma=","; [ "$i" -eq "$((${#metrics[@]} - 1))" ] && comma=""
      printf '{"id":"%s","value":"%s"}%s' "$(json_escape "$id")" "$(json_escape "$value")" "$comma"
    done
    printf ']}'
  } > "$run_dir/metrics.json"
  echo "Validation written to ${run_dir#$repo_dir/}/validation.json"
  case "$status" in PASS|NOT_TESTED) return 0;; PARTIAL) return 1;; *) return 1;; esac
}

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  for id in mongo nrf amf smf upf ausf udm udr pcf ng_setup ue_registration pdu_internet pdu_ims ue_internet_ip ue_ims_ip ue_internet_tun ue_ims_tun data_ping ims_database pcscf icscf scscf ims_dns pcscf_reachable_over_ims sip_register; do
    add_check "$id" NOT_TESTED "dry-run mode"
  done
  write_outputs
  exit 0
fi

for svc in mongo nrf amf smf upf ausf udm udr pcf; do
  running "$svc" && add_check "$svc" PASS "$svc container running" || add_check "$svc" FAIL "$svc container not running"
done

for svc in gnb ue amf smf upf pcscf icscf scscf dns sip-register; do
  compose logs --no-color "$svc" >"$run_dir/logs/$svc.log" 2>/dev/null || true
done

if logs_have gnb 'NG Setup procedure is successful|NG Setup.*successful|NG-Setup.*successful' || logs_have amf 'gNB-N2 accepted|Number of gNBs is now 1'; then
  add_check ng_setup PASS "NG Setup evidence found"
  add_claim "gNB connected to AMF"
else
  add_check ng_setup FAIL "NG Setup evidence not found"
fi

if logs_have ue 'Registration is successful|Initial Registration is successful|5GMM.*Registered'; then
  add_check ue_registration PASS "UE registration evidence found"
  add_claim "5G UE registered"
else
  add_check ue_registration FAIL "UE registration evidence not found"
fi

if logs_have ue 'PDU Session.*internet.*successful|internet.*PDU Session.*successful|PDU Session Establishment is successful.*internet' || logs_have smf 'internet'; then
  add_check pdu_internet PASS "internet PDU session evidence found"
  add_claim "Internet PDU session established"
else
  add_check pdu_internet FAIL "internet PDU session evidence not found"
fi

if logs_have ue 'PDU Session.*ims.*successful|ims.*PDU Session.*successful|PDU Session Establishment is successful.*ims' || logs_have smf 'ims'; then
  add_check pdu_ims PASS "IMS PDU session evidence found"
  add_claim "IMS PDU session established"
else
  add_check pdu_ims FAIL "IMS PDU session evidence not found"
fi

ip_output="$(exec_out ue ip -4 -o addr show || true)"
printf '%s\n' "$ip_output" > "$run_dir/logs/ue-ip-addr.log"
internet_if="$(printf '%s\n' "$ip_output" | awk '/10\.60\./ {print $2; exit}')"
ims_if="$(printf '%s\n' "$ip_output" | awk '/10\.61\./ {print $2; exit}')"
internet_ip="$(printf '%s\n' "$ip_output" | awk '/10\.60\./ {print $4; exit}' | cut -d/ -f1)"
ims_ip="$(printf '%s\n' "$ip_output" | awk '/10\.61\./ {print $4; exit}' | cut -d/ -f1)"

if [ -n "$internet_ip" ]; then add_check ue_internet_ip PASS "internet IP assigned: $internet_ip"; add_metric ue_internet_ip "$internet_ip"; add_claim "Internet UE IP assigned"; else add_check ue_internet_ip FAIL "internet IP not found"; fi
if [ -n "$ims_ip" ]; then add_check ue_ims_ip PASS "IMS IP assigned: $ims_ip"; add_metric ue_ims_ip "$ims_ip"; add_claim "IMS UE IP assigned"; else add_check ue_ims_ip FAIL "IMS IP not found"; fi
if [ -n "$internet_if" ]; then add_check ue_internet_tun PASS "internet TUN interface: $internet_if"; add_metric ue_internet_tun "$internet_if"; else add_check ue_internet_tun FAIL "internet TUN interface not found"; fi
if [ -n "$ims_if" ]; then add_check ue_ims_tun PASS "IMS TUN interface: $ims_if"; add_metric ue_ims_tun "$ims_if"; else add_check ue_ims_tun FAIL "IMS TUN interface not found"; fi

if [ -n "$internet_if" ] && exec_ok ue ping -I "$internet_if" -c 3 -W 2 "${PING_TARGET:-10.60.0.1}"; then
  add_check data_ping PASS "ping via $internet_if succeeded"
  add_claim "Data ping succeeded"
else
  add_check data_ping FAIL "ping via internet PDU failed"
fi

running ims-database && add_check ims_database PASS "IMS database running" || add_check ims_database FAIL "IMS database not running"
for svc in pcscf icscf scscf; do running "$svc" && add_check "$svc" PASS "$svc running" || add_check "$svc" FAIL "$svc not running"; done

if [ -n "$ims_if" ] && [ -n "$ims_ip" ]; then
  for ip in 10.50.0.20 10.50.0.22 10.50.0.23 10.50.0.30; do
    compose exec -T ue ip route replace "$ip/32" dev "$ims_if" src "$ims_ip" >/dev/null 2>&1 || true
  done
fi

if [ -n "$ims_if" ] && exec_ok ue ping -I "$ims_if" -c 1 -W 2 10.50.0.30; then
  if compose run --rm --no-deps --entrypoint python3 sip-register -c 'import os, socket, struct, sys; server="10.50.0.30"; name=os.environ.get("IMS_DOMAIN", "ims.mnc001.mcc001.3gppnetwork.org"); q=b"".join(bytes([len(p)])+p.encode() for p in name.split("."))+b"\0"; pkt=b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"+q+b"\x00\x01\x00\x01"; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(3); s.sendto(pkt,(server,53)); data,_=s.recvfrom(512); sys.exit(0 if data[:2] == b"\x12\x34" and struct.unpack("!H", data[6:8])[0] > 0 else 1)' >/dev/null 2>&1; then
    add_check ims_dns PASS "IMS DNS resolved through IMS path"
    add_claim "IMS DNS resolved"
  else
    add_check ims_dns FAIL "IMS DNS query failed through IMS path"
  fi
else
  add_check ims_dns FAIL "IMS DNS not reachable through IMS TUN"
fi

if [ -n "$ims_if" ] && exec_ok ue ping -I "$ims_if" -c 1 -W 2 10.50.0.20; then
  add_check pcscf_reachable_over_ims PASS "P-CSCF reached through IMS TUN $ims_if"
  add_claim "P-CSCF reached through IMS data path"
else
  add_check pcscf_reachable_over_ims FAIL "P-CSCF not reachable through IMS TUN"
fi

if [ -n "$ims_if" ] && [ -n "$ims_ip" ]; then
  if compose run --rm --no-deps sip-register >"$run_dir/logs/sip-register-run.log" 2>&1; then
    compose logs --no-color sip-register >"$run_dir/logs/sip-register.log" 2>/dev/null || true
  else
    compose logs --no-color sip-register >"$run_dir/logs/sip-register.log" 2>/dev/null || true
  fi
fi

if grep -Eiq 'SIP_CLIENT_INITIAL_REGISTER_SENT' "$run_dir/logs/sip-register-run.log" 2>/dev/null && \
   grep -Eiq 'SIP_CLIENT_CHALLENGE_RECEIVED code=401' "$run_dir/logs/sip-register-run.log" 2>/dev/null && \
   grep -Eiq 'SIP_CLIENT_AUTH_REGISTER_SENT' "$run_dir/logs/sip-register-run.log" 2>/dev/null && \
   grep -Eiq 'SIP_CLIENT_FINAL_RESPONSE code=200' "$run_dir/logs/sip-register-run.log" 2>/dev/null && \
   grep -Eiq 'SIP_REGISTER_RESULT=PASS final_code=200' "$run_dir/logs/sip-register-run.log" 2>/dev/null && \
   logs_have pcscf 'P-CSCF_FORWARD_REGISTER' && logs_have icscf 'I-CSCF_FORWARD_REGISTER' && logs_have scscf 'SCSCF_INITIAL_REGISTER|SCSCF_AUTH_REGISTER|SCSCF_SENT_200_OK'; then
  add_check sip_register PASS "REGISTER, 401, authenticated REGISTER, and final 200 OK observed"
  add_metric sip_final_code "200"
  add_claim "SIP REGISTER succeeded"
else
  final_code="$(grep -Eo 'SIP_CLIENT_FINAL_RESPONSE code=[0-9]+' "$run_dir/logs/sip-register-run.log" 2>/dev/null | tail -n1 | cut -d= -f2 || true)"
  [ -n "$final_code" ] && add_metric sip_final_code "$final_code"
  add_check sip_register FAIL "SIP REGISTER authenticated 200 OK evidence missing"
fi

rm -f /tmp/lain5g-vonr-validate.$$
write_outputs
