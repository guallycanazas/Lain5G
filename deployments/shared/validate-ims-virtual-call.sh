#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: validate-ims-virtual-call.sh <deployment-path> <env-file>" >&2
  exit 2
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
scenario_dir="$repo_dir/$1"
env_file="$2"
if [ ! -f "$scenario_dir/$env_file" ]; then
  if [ "${env_file##*/}" != .env ]; then
    echo "IMS environment file not found: $env_file" >&2
    exit 2
  fi
  env_file="${env_file%/*}/.env.example"
  [ -f "$scenario_dir/$env_file" ] || {
    echo "IMS environment file or example not found" >&2
    exit 2
  }
fi

if [ "$1" = deployments/5g-sa-x310 ]; then
  occupied_addresses="$(docker network inspect --format '{{range .Containers}}{{println .IPv4Address}}{{end}}' lain5g-lab-5g-sa-x310-core 2>/dev/null || true)"
  if printf '%s\n' "$occupied_addresses" | grep -Eq '^10\.20\.0\.(19|20|22|23|30|31|32)/'; then
    echo "IMS_VIRTUAL_CALL_NOT_TESTED reason=shared_network_address_occupied"
    echo "IMS virtual call check was skipped: a fixed IMS address on the shared 5G SA network is occupied. Stop the conflicting profile before validating this IMS path. No containers were started."
    exit 2
  fi
fi

compose() {
  (cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile sip "$@")
}

services=(ims-database pcscf icscf scscf dns)
started_here=()
for service in "${services[@]}"; do
  if [ -z "$(compose ps --status running -q "$service" 2>/dev/null || true)" ]; then
    started_here+=("$service")
  fi
done

cleanup() {
  for service in "${started_here[@]}"; do
    compose stop "$service" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT

compose up -d "${services[@]}"
compose run --rm virtual-phones
