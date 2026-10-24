#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose --profile rf stop gnb-x310 && docker compose down --remove-orphans"; exit 0; fi
route_image="${LAIN5G_ROUTE_HELPER_IMAGE:-lain5g-lab/srsranproject-uhd:local}"
route_state="$scenario_dir/.ue-route-active"
host_route(){ docker run --rm --network host --cap-add NET_ADMIN "$route_image" ip route "$@"; }
if [ -f "$route_state" ]; then
  route_state_tmp="$route_state.tmp"
  : > "$route_state_tmp"
  while IFS= read -r ue_subnet && IFS= read -r upf_ip; do
    if [[ ! "$ue_subnet" =~ ^[0-9.]+/[0-9]+$ || ! "$upf_ip" =~ ^[0-9.]+$ ]]; then
      echo "WARNING: invalid managed host route state; preserving it for inspection" >&2
      printf '%s\n%s\n' "$ue_subnet" "$upf_ip" >> "$route_state_tmp"
      continue
    fi
    current_route="$(host_route show exact "$ue_subnet" 2>/dev/null | head -n1 || true)"
    if [[ "$current_route" == *"via $upf_ip"* ]]; then
      if host_route del "$ue_subnet" via "$upf_ip" 2>/dev/null; then
        echo "Removed host UE route: $ue_subnet via $upf_ip"
      else
        echo "WARNING: could not remove the managed host UE route $ue_subnet" >&2
        printf '%s\n%s\n' "$ue_subnet" "$upf_ip" >> "$route_state_tmp"
      fi
    fi
  done < "$route_state"
  if [ -s "$route_state_tmp" ]; then mv "$route_state_tmp" "$route_state"; else rm -f "$route_state_tmp" "$route_state"; fi
fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf stop gnb-x310 >/dev/null 2>&1 || true)
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml down --remove-orphans)
rm -f "$scenario_dir/.rf-active"
