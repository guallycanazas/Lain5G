#!/usr/bin/env bash
set -euo pipefail

network="lain5g-lab-5g-sa-x310-core"
subnet="10.20.0.0/24"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: inspect or create Docker network $network ($subnet)"
  exit 0
fi

if docker network inspect "$network" >/dev/null 2>&1; then
  current_subnet="$(docker network inspect --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' "$network")"
  if [ "$current_subnet" != "$subnet" ]; then
    echo "5G SA core network has unexpected subnet: $current_subnet (expected $subnet)" >&2
    exit 2
  fi
  exit 0
fi

docker network create --driver bridge --subnet "$subnet" "$network" >/dev/null
echo "Created shared 5G SA core network $network ($subnet)"
