#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"

if [ -f "$scenario_dir/.env" ]; then
  set -a
  source "$scenario_dir/.env"
  set +a
fi

checks=()
validated_claims=()

add_check() {
  local id="$1"
  local status="$2"
  local detail="$3"
  checks+=("$id|$status|$detail")
  printf '%-28s %s %s\n' "$id" "$status" "$detail"
}

compose() {
  (cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml "$@")
}

is_running() {
  local service="$1"
  [ -n "$(compose ps --status running -q "$service" 2>/dev/null)" ]
}

logs_have() {
  local service="$1"
  local pattern="$2"
  local output
  output="$(compose logs --no-color "$service" 2>/dev/null || true)"
  grep -Eiq "$pattern" <<< "$output"
}

run_exec() {
  local service="$1"
  shift
  compose exec -T "$service" "$@" >/tmp/lain5g-validate.$$ 2>&1
}

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  for id in mongo nrf amf smf upf ausf udm udr pcf ng_setup ue_registration pdu_session ue_tun ue_ip ping; do
    add_check "$id" "NOT_TESTED" "dry-run mode"
  done
else
  if compose exec -T mongo mongosh --quiet --eval "db.adminCommand('ping').ok" >/dev/null 2>&1; then
    add_check "mongo" "PASS" "MongoDB responds to ping"
  else
    add_check "mongo" "FAIL" "MongoDB did not respond"
  fi

  for service in nrf amf smf upf ausf udm udr pcf; do
    if is_running "$service"; then
      add_check "$service" "PASS" "container is running"
    else
      add_check "$service" "FAIL" "container is not running"
    fi
  done

  if logs_have gnb 'NG Setup procedure is successful|NG Setup.*successful|NG-Setup.*successful'; then
    add_check "ng_setup" "PASS" "gNB reports successful NG setup"
    validated_claims+=("gNB connected to AMF")
  elif is_running gnb; then
    add_check "ng_setup" "WARNING" "gNB is running but NG setup evidence was not found"
  else
    add_check "ng_setup" "FAIL" "gNB is not running"
  fi

  if logs_have ue 'Initial Registration is successful|Registration is successful|Registration.*successful|5GMM.*Registered'; then
    add_check "ue_registration" "PASS" "UE registration evidence found"
    validated_claims+=("UE registered")
  elif is_running ue; then
    add_check "ue_registration" "WARNING" "UE is running but registration evidence was not found"
  else
    add_check "ue_registration" "FAIL" "UE is not running"
  fi

  if logs_have ue 'PDU Session Establishment is successful|PDU session.*successful|PDU Session.*established'; then
    add_check "pdu_session" "PASS" "PDU session evidence found"
    validated_claims+=("PDU session established")
  elif is_running ue; then
    add_check "pdu_session" "WARNING" "UE is running but PDU session evidence was not found"
  else
    add_check "pdu_session" "FAIL" "UE is not running"
  fi

  if run_exec ue ip link show uesimtun0; then
    add_check "ue_tun" "PASS" "uesimtun0 exists in UE container"
    validated_claims+=("UERANSIM TUN interface created")
  else
    add_check "ue_tun" "FAIL" "uesimtun0 not found in UE container"
  fi

  if run_exec ue ip -4 addr show uesimtun0 && grep -Eq 'inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' /tmp/lain5g-validate.$$; then
    ue_ip="$(grep -Eo 'inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' /tmp/lain5g-validate.$$ | awk '{print $2}' | head -n 1)"
    add_check "ue_ip" "PASS" "UE IP assigned: $ue_ip"
    validated_claims+=("UE IP assigned")
  else
    add_check "ue_ip" "FAIL" "No IPv4 address found on uesimtun0"
  fi

  ping_target="${PING_TARGET:-8.8.8.8}"
  if run_exec ue ping -I uesimtun0 -c 3 -W 2 "$ping_target"; then
    add_check "ping" "PASS" "Ping to $ping_target succeeded from UE"
    validated_claims+=("ping succeeded")
  elif is_running ue; then
    add_check "ping" "FAIL" "Ping to $ping_target failed from UE"
  else
    add_check "ping" "NOT_TESTED" "UE is not running"
  fi
fi

rm -f /tmp/lain5g-validate.$$

latest_run="$(find "$repo_dir/runs" -mindepth 1 -maxdepth 1 -type d -name 'run-*' | sort | tail -n 1 || true)"
if [ -z "$latest_run" ]; then
  run_id="run-$(date -u +%Y%m%d-%H%M%S)"
  latest_run="$repo_dir/runs/$run_id"
  mkdir -p "$latest_run/logs"
  git_commit="$(git -C "$repo_dir" rev-parse --short HEAD 2>/dev/null || true)"
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat > "$latest_run/metadata.json" <<JSON
{
  "run_id": "$run_id",
  "scenario": "5g-sa",
  "deployment_path": "deployments/5g-sa",
  "started_at": "$now",
  "finished_at": "",
  "status": "validation-only",
  "git_commit": "$git_commit",
  "validated_claims": []
}
JSON
  printf '{\n  "created_at": "%s",\n  "metrics": []\n}\n' "$now" > "$latest_run/metrics.json"
fi

validation_file="$latest_run/validation.json"
{
  printf '{\n  "scenario": "5g-sa",\n  "checked_at": "%s",\n  "checks": [\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for i in "${!checks[@]}"; do
    IFS='|' read -r id status detail <<< "${checks[$i]}"
    detail_json="${detail//\\/\\\\}"
    detail_json="${detail_json//\"/\\\"}"
    comma=","; [ "$i" -eq "$((${#checks[@]} - 1))" ] && comma=""
    printf '    {"id": "%s", "status": "%s", "detail": "%s"}%s\n' "$id" "$status" "$detail_json" "$comma"
  done
  printf '  ]\n}\n'
} > "$validation_file"

if [ "${#validated_claims[@]}" -gt 0 ] && [ -f "$latest_run/metadata.json" ]; then
  claims_json="$(printf '"%s",' "${validated_claims[@]}")"
  claims_json="[${claims_json%,}]"
  tmp_file="$(mktemp)"
  sed "s/\"validated_claims\": \[\]/\"validated_claims\": $claims_json/" "$latest_run/metadata.json" > "$tmp_file"
  mv "$tmp_file" "$latest_run/metadata.json"
fi

echo "Validation written to ${validation_file#$repo_dir/}"
