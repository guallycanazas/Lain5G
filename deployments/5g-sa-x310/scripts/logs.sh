#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
service="${SERVICE:-}"
case "$service" in ""|mongo|nrf|ausf|udm|udr|pcf|upf|smf|amf|gnb-x310) ;; *) echo "Unknown service: $service" >&2; exit 2;; esac
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then echo "DRY RUN: docker compose logs ${service}"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf logs --no-color ${service})
