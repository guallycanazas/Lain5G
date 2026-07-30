#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then echo "DRY RUN: docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml stop"; exit 0; fi
(cd "$scenario_dir" && docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml stop)

latest_run=""
for metadata in "$repo_dir"/runs/run-*/metadata.json; do
  [ -f "$metadata" ] || continue
  grep -Eq '"scenario"[[:space:]]*:[[:space:]]*"4g-lte-sim"' "$metadata" && latest_run="$(dirname "$metadata")"
done
if [ -n "$latest_run" ]; then
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  tmp_file="$(mktemp)"
  sed -E -e "s/\"finished_at\"[[:space:]]*:[[:space:]]*\"\"/\"finished_at\":\"$finished_at\"/" \
      -e 's/"status"[[:space:]]*:[[:space:]]*"started"/"status":"stopped"/' \
      "$latest_run/metadata.json" > "$tmp_file"
  mv "$tmp_file" "$latest_run/metadata.json"
fi
