#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
services=(mongo nrf ausf udm udr pcf upf smf amf)
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose up -d ${services[*]}"; exit 0; fi
simulation_project="lain5g-lab-5g-sa"
simulation_network="lain5g-lab-5g-sa-core"
if [ -n "$(docker ps -aq --filter "label=com.docker.compose.project=$simulation_project")" ] || docker network inspect "$simulation_network" >/dev/null 2>&1; then
  echo "Switching from 5G SA simulation to 5G SA X310 core..."
  "$repo_dir/deployments/5g-sa/scripts/stop.sh"
  echo "5G SA simulation stopped; volumes and data were preserved."
fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml up -d "${services[@]}")

set -a
source "$env_file"
set +a

upf_ip="$(cd "$scenario_dir" && docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lain5g-lab-5g-sa-x310-upf 2>/dev/null || true)"
if [ -z "$upf_ip" ]; then
  echo "WARNING: UPF IP not found; host UE route was not installed" >&2
  exit 0
fi

route_cmd=(ip route replace)
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  if sudo -n true 2>/dev/null; then
    route_cmd=(sudo -n ip route replace)
  else
    echo "WARNING: sudo is required to install host UE route" >&2
    exit 0
  fi
fi

ue_subnet="${UE_SUBNET:-10.45.0.0/16}"
if "${route_cmd[@]}" "$ue_subnet" via "$upf_ip" 2>/dev/null; then
  echo "Installed host route: $ue_subnet via $upf_ip"
else
  echo "WARNING: core is running, but host route $ue_subnet could not be installed from this network namespace" >&2
fi
