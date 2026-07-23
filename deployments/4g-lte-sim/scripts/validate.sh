#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
checks=()
claims=()
add_check(){ checks+=("$1|$2|$3"); printf '%-24s %s %s\n' "$1" "$2" "$3"; }
compose(){ (cd "$scenario_dir" && docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml "$@"); }
running(){ [ -n "$(compose ps --status running -q "$1" 2>/dev/null)" ]; }
logs_have(){
  local status
  set +o pipefail
  (cd "$scenario_dir" && timeout 10s docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml logs --no-color "$1" 2>/dev/null) | grep -Eiq -m1 "$2"
  status=$?
  set -o pipefail
  return "$status"
}
container_file_have(){ compose exec -T "$1" sh -lc 'grep -Eiq "$1" "$2"' sh "$3" "$2" 2>/dev/null; }

latest=""
for metadata in "$repo_dir"/runs/run-*/metadata.json; do
  [ -f "$metadata" ] || continue
  grep -q '"scenario":"4g-lte-sim"' "$metadata" && latest="$(dirname "$metadata")"
done
[ -n "$latest" ] || { latest="$repo_dir/runs/run-$(date -u +%Y%m%d-%H%M%S)"; mkdir -p "$latest/logs"; }
mkdir -p "$latest/logs"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  for id in mongo mme hss sgwc sgwu pgwc pgwu pcrf s1_setup ue_registration default_bearer ue_ip ue_tun data_ping; do add_check "$id" NOT_TESTED "dry-run mode"; done
else
  for svc in mongo mme hss sgwc sgwu pgwc pgwu pcrf; do running "$svc" && add_check "$svc" PASS "container is running" || add_check "$svc" FAIL "container is not running"; done
  { container_file_have mme /var/log/open5gs/mme.log 'eNB-S1 accepted|Number of eNBs is now 1' || logs_have enb 'S1 Setup|S1AP.*Setup|MME connection|S1 connection'; } && { add_check s1_setup PASS "eNB/MME S1 evidence found"; claims+=("eNB connected to MME"); } || add_check s1_setup WARNING "S1 evidence not found"
  { container_file_have mme /var/log/open5gs/mme.log 'Attach complete' || logs_have ue 'Attach.*complete|RRC Connected|Network attach successful|Received Attach Accept'; } && { add_check ue_registration PASS "srsUE registration evidence found"; claims+=("LTE UE registered"); } || add_check ue_registration WARNING "UE registration evidence not found"
  { logs_have ue 'Registered EPS bearer|Default EPS bearer|bearer.*established|Network attach successful' || logs_have enb 'InitialContextSetupResponse|New tunnel created|DRB1|User .*connected'; } && { add_check default_bearer PASS "default bearer evidence found"; claims+=("Default bearer established"); } || add_check default_bearer WARNING "bearer evidence not found"
  compose exec -T ue ip addr 2>/dev/null | grep -Eq 'tun|10\.57\.' && { add_check ue_ip PASS "UE IP evidence found"; claims+=("UE IP assigned"); } || add_check ue_ip WARNING "UE IP evidence not found"
  compose exec -T ue ip link 2>/dev/null | grep -Eq 'tun|srs' && add_check ue_tun PASS "UE network interface evidence found" || add_check ue_tun WARNING "UE network interface evidence not found"
  compose exec -T ue ping -c 1 -W 2 10.57.0.1 >/dev/null 2>&1 && { add_check data_ping PASS "UE ping succeeded"; claims+=("Data ping succeeded"); } || add_check data_ping WARNING "UE ping not validated"
fi

status=PASS
for check in "${checks[@]}"; do
  IFS='|' read -r _ st _ <<< "$check"
  { [ "$st" = FAIL ] || [ "$st" = WARNING ]; } && status=FAIL
done
{
  printf '{"scenario":"4g-lte-sim","status":"%s","checked_at":"%s","checks":[' "$status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for i in "${!checks[@]}"; do
    IFS='|' read -r id st detail <<< "${checks[$i]}"
    comma=","; [ "$i" -eq "$((${#checks[@]} - 1))" ] && comma=""
    detail="${detail//\"/\\\"}"
    printf '{"id":"%s","status":"%s","detail":"%s"}%s' "$id" "$st" "$detail" "$comma"
  done
  printf ']}'
} > "$latest/validation.json"
echo "Validation written to ${latest#$repo_dir/}"
