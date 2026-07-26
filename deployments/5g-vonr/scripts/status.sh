#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose --env-file .env -f docker-compose.yml --profile sip ps"; exit 0; fi
if [ -t 1 ]; then
  (cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml --profile sip ps)
else
  (cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml --profile sip ps --format '{"Name":"{{.Name}}","Service":"{{.Service}}","State":"{{.State}}","Status":"{{.Status}}"}')
fi
