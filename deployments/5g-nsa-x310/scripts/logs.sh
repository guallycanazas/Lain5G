#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
service="${SERVICE:-}"
case "$service" in ""|mongo|mme|hss|sgwc|sgwu|pgwc|pgwu|pcrf|enb-nsa-x310) ;; *) echo "Unknown service: $service" >&2; exit 2;; esac
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose logs ${service}"; exit 0; fi
args=(logs --no-color --tail "${LAIN5G_LOG_TAIL_LINES:-500}")
[ -z "$service" ] || args+=("$service")
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf "${args[@]}")
