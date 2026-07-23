#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
service="${SERVICE:-}"
case "$service" in ""|mongo|subscriber-provisioner|nrf|amf|smf|upf|ausf|udm|udr|pcf|gnb|ue|ims-database|ims-provisioner|pcscf|icscf|scscf|dns|sip-register) ;; *) echo "Unknown service: $service" >&2; exit 2;; esac
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose logs ${service}"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml --profile sip logs --no-color ${service})
