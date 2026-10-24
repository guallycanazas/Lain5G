#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
service="${SERVICE:-}"
case "$service" in ""|mongo|mme|hss|sgwc|sgwu|pgwc|pgwu|pcrf|subscriber-provisioner|enb|ue) ;; *) echo "Unknown service: $service" >&2; exit 2;; esac
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose logs ${service}"; exit 0; fi
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
compose(){ (cd "$scenario_dir" && docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml "$@"); }

latest_run=""
for metadata in "$repo_dir"/runs/run-*/metadata.json; do
  [ -f "$metadata" ] || continue
  grep -Eq '"scenario"[[:space:]]*:[[:space:]]*"4g-lte-sim"' "$metadata" && latest_run="$(dirname "$metadata")"
done

if [ -n "$latest_run" ] && ! compose ps --status running -q 2>/dev/null | grep -q .; then
  if [ -n "$service" ] && [ -s "$latest_run/logs/$service.log" ]; then
    cat "$latest_run/logs/$service.log"
  elif [ -s "$latest_run/logs/docker-compose.log" ]; then
    cat "$latest_run/logs/docker-compose.log"
  else
    compose logs --no-color ${service}
  fi
else
  compose logs --no-color ${service}
fi
