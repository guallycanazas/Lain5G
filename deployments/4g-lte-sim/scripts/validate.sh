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
registration_ready(){ container_file_have mme /var/log/open5gs/mme.log 'Attach complete' || logs_have ue 'Attach.*complete|RRC Connected|Network attach successful|Received Attach Accept'; }

latest=""
for metadata in "$repo_dir"/runs/run-*/metadata.json; do
  [ -f "$metadata" ] || continue
  grep -q '"scenario":"4g-lte-sim"' "$metadata" && latest="$(dirname "$metadata")"
done
[ -n "$latest" ] || {
  run_id="run-$(date -u +%Y%m%d-%H%M%S)"
  latest="$repo_dir/runs/$run_id"
  mkdir -p "$latest/logs"
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git_commit="$(git -C "$repo_dir" rev-parse --short HEAD 2>/dev/null || true)"
  printf '{"run_id":"%s","scenario":"4g-lte-sim","deployment_path":"deployments/4g-lte-sim","started_at":"%s","finished_at":"","status":"validation-only","git_commit":"%s","validated_claims":[]}\n' "$run_id" "$now" "$git_commit" > "$latest/metadata.json"
  printf '{"created_at":"%s","metrics":[]}\n' "$now" > "$latest/metrics.json"
}
mkdir -p "$latest/logs"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  for id in mongo mme hss sgwc sgwu pgwc pgwu pcrf s1_setup ue_registration default_bearer ue_ip ue_tun data_ping; do add_check "$id" NOT_TESTED "dry-run mode"; done
else
  for svc in mongo mme hss sgwc sgwu pgwc pgwu pcrf; do running "$svc" && add_check "$svc" PASS "container is running" || add_check "$svc" FAIL "container is not running"; done
  if running ue; then
    for _ in 1 2 3 4 5 6; do
      registration_ready && break
      sleep 5
    done
  fi
  { container_file_have mme /var/log/open5gs/mme.log 'eNB-S1 accepted|Number of eNBs is now 1' || logs_have enb 'S1 Setup|S1AP.*Setup|MME connection|S1 connection'; } && { add_check s1_setup PASS "eNB/MME S1 evidence found"; claims+=("eNB connected to MME"); } || add_check s1_setup WARNING "S1 evidence not found"
  registration_ready && { add_check ue_registration PASS "srsUE registration evidence found in MME/UE logs"; claims+=("LTE UE registered"); } || add_check ue_registration WARNING "UE registration evidence not found"
  { container_file_have mme /var/log/open5gs/mme.log 'Number of MME-Sessions is now [1-9][0-9]*' || logs_have ue 'Registered EPS bearer|Default EPS bearer|bearer.*established|Network attach successful' || logs_have enb 'InitialContextSetupResponse|New tunnel created|DRB1|User .*connected'; } && { add_check default_bearer PASS "default bearer evidence found in MME/RAN logs"; claims+=("Default bearer established"); } || add_check default_bearer WARNING "bearer evidence not found"
  ue_ip="$(compose exec -T ue ip -o -4 addr show dev tun_srsue 2>/dev/null | grep -Eo '10\.57\.[0-9]+\.[0-9]+' | head -n 1 || true)"
  [ -n "$ue_ip" ] && { add_check ue_ip PASS "UE IP assigned on tun_srsue: $ue_ip"; claims+=("UE IP assigned"); } || add_check ue_ip WARNING "UE IPv4 address not found on tun_srsue"
  compose exec -T ue ip link show dev tun_srsue >/dev/null 2>&1 && add_check ue_tun PASS "tun_srsue exists in UE container" || add_check ue_tun WARNING "tun_srsue not found in UE container"
  compose exec -T ue ping -I tun_srsue -c 3 -W 2 10.57.0.1 >/dev/null 2>&1 && { add_check data_ping PASS "Ping to 10.57.0.1 succeeded through tun_srsue"; claims+=("Data ping succeeded"); } || add_check data_ping WARNING "Ping through tun_srsue was not validated"
fi

status=PASS
for check in "${checks[@]}"; do
  IFS='|' read -r _ st _ <<< "$check"
  if [ "$st" = FAIL ]; then
    status=FAIL
  elif [ "$st" = WARNING ] && [ "$status" = PASS ]; then
    status=WARNING
  fi
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
