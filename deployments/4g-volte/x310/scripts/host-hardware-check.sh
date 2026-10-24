#!/usr/bin/env bash
set -euo pipefail

if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: X310 host hardware-check plan; no Docker, network, device, UHD, or file access was performed"
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../../.." && pwd)"
image="${LAIN5G_UHD_IMAGE:-lain5g-lab/srsran4g-uhd:local}"

if docker image inspect "$image" >/dev/null 2>&1; then
  exec docker run --rm --network host \
    -v "$repo_dir:$repo_dir" -w "$repo_dir" "$image" \
    deployments/4g-volte/x310/scripts/hardware-check.sh
fi

exec "$script_dir/hardware-check.sh"
