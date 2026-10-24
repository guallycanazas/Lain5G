#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
env_file="$scenario_dir/.env"
services=(mongo nrf ausf udm udr pcf upf smf amf ims-database ims-provisioner scscf icscf pcscf dns)
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose up -d ${services[*]}"; exit 0; fi
[ -f "$env_file" ] || { echo "Missing private environment. Run: ./lain5g scenario setup 5g-sa-x310" >&2; exit 2; }
set -a
source "$env_file"
set +a
[ -n "${IMS_AUTH_PASSWORD:-}" ] || { echo "Missing IMS_AUTH_PASSWORD. Run: ./lain5g scenario setup 5g-sa-x310" >&2; exit 2; }
chmod 600 "$env_file"
"$scenario_dir/scripts/ensure-core-network.sh"
route_image="${LAIN5G_ROUTE_HELPER_IMAGE:-lain5g-lab/srsranproject-uhd:local}"
route_state="$scenario_dir/.ue-route-active"
host_route(){ docker run --rm --network host --cap-add NET_ADMIN "$route_image" ip route "$@"; }
simulation_project="lain5g-lab-5g-sa"
simulation_network="lain5g-lab-5g-sa-core"
if [ -n "$(docker ps -aq --filter "label=com.docker.compose.project=$simulation_project")" ] || docker network inspect "$simulation_network" >/dev/null 2>&1; then
  echo "Switching from 5G SA simulation to 5G SA X310 core..."
  "$repo_dir/deployments/5g-sa/scripts/stop.sh"
  echo "5G SA simulation stopped; volumes and data were preserved."
fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml up -d "${services[@]}")

upf_ip="$(cd "$scenario_dir" && docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lain5g-lab-5g-sa-x310-upf 2>/dev/null || true)"
if [ -z "$upf_ip" ]; then
  echo "WARNING: UPF IP not found; host UE route was not installed" >&2
  exit 0
fi

ue_subnets=("${UE_SUBNET:-10.45.0.0/16}" "${UE_IMS_SUBNET:-10.46.0.0/16}")
route_state_tmp="$route_state.tmp"
: > "$route_state_tmp"
for ue_subnet in "${ue_subnets[@]}"; do
  existing_route="$(host_route show exact "$ue_subnet" 2>/dev/null | head -n1 || true)"
  managed_upf=""
  if [ -f "$route_state" ]; then
    while IFS= read -r previous_subnet && IFS= read -r previous_upf; do
      if [ "$previous_subnet" = "$ue_subnet" ]; then managed_upf="$previous_upf"; fi
    done < "$route_state"
  fi
  if [ -n "$existing_route" ] && [[ "$existing_route" != *"via $upf_ip"* ]] && { [ -z "$managed_upf" ] || [[ "$existing_route" != *"via $managed_upf"* ]]; }; then
    echo "WARNING: core is running, but an existing host route for $ue_subnet was preserved" >&2
  elif host_route replace "$ue_subnet" via "$upf_ip" 2>/dev/null; then
    printf '%s\n%s\n' "$ue_subnet" "$upf_ip" >> "$route_state_tmp"
    echo "Installed host UE route: $ue_subnet via $upf_ip"
  else
    echo "WARNING: core is running, but Docker could not install the host UE route $ue_subnet" >&2
  fi
done
if [ -s "$route_state_tmp" ]; then mv "$route_state_tmp" "$route_state"; else rm -f "$route_state_tmp" "$route_state"; fi
