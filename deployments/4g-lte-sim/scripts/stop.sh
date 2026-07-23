#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml stop"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml stop)
