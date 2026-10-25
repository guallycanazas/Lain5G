#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
service="${SERVICE:-}"
case "$service" in ""|mongo|mme|hss|sgwc|sgwu|pgwc|pgwu|pcrf|ims-database|pcscf|icscf|scscf|dns|subscriber-provisioner|ims-provisioner|enb|ue) ;; *) echo "Unknown service: $service" >&2; exit 2;; esac
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose logs ${service}"; exit 0; fi
env_file=../common/.env
if [ ! -f "$scenario_dir/$env_file" ]; then env_file=../common/.env.example; fi
(cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml logs --no-color ${service})
