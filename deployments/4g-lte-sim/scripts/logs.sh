#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
service="${SERVICE:-}"
case "$service" in ""|mongo|mme|hss|sgwc|sgwu|pgwc|pgwu|pcrf|subscriber-provisioner|enb|ue) ;; *) echo "Unknown service: $service" >&2; exit 2;; esac
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose logs ${service}"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml logs --no-color ${service})
