#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose --env-file ../common/.env -f docker-compose.yml up -d EPC + IMS"; exit 0; fi
env_file="$scenario_dir/../common/.env"
[ -f "$env_file" ] || { echo "Missing private environment. Run: ./lain5g scenario setup 4g-lte-x310" >&2; exit 2; }

set -a
source "$env_file"
set +a
for name in SUBSCRIBER_KEY SUBSCRIBER_OPC IMS_AUTH_PASSWORD; do
  [ -n "${!name:-}" ] || { echo "Missing $name. Run: ./lain5g scenario setup 4g-lte-x310" >&2; exit 2; }
done
chmod 600 "$env_file"
(cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml up -d)

pgwu_ip="$(cd "$scenario_dir" && docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lain5g-lab-4g-lte-x310-pgwu 2>/dev/null || true)"
if [ -z "$pgwu_ip" ]; then
  echo "WARNING: PGW-U IP not found; host UE routes were not installed" >&2
  exit 0
fi

route_cmd=(ip route replace)
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  if sudo -n true 2>/dev/null; then
    route_cmd=(sudo -n ip route replace)
  else
    echo "WARNING: sudo is required to install host UE routes" >&2
    exit 0
  fi
fi

for subnet in "${UE_INTERNET_SUBNET:-10.55.0.0/16}" "${UE_IMS_SUBNET:-}"; do
  [ -n "$subnet" ] || continue
  if "${route_cmd[@]}" "$subnet" via "$pgwu_ip" 2>/dev/null; then
    echo "Installed host route: $subnet via $pgwu_ip"
  else
    echo "WARNING: core is running, but host route $subnet could not be installed from this network namespace" >&2
  fi
done
