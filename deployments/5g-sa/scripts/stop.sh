#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"

if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: docker compose --env-file .env -f docker-compose.yml down --remove-orphans"
  exit 0
fi

(cd "$scenario_dir" && docker compose --env-file .env -f docker-compose.yml down --remove-orphans)

latest_run=""
for metadata in "$repo_dir"/runs/run-*/metadata.json; do
  [ -f "$metadata" ] || continue
  grep -Eq '"scenario"[[:space:]]*:[[:space:]]*"5g-sa"' "$metadata" && latest_run="$(dirname "$metadata")"
done
if [ -n "$latest_run" ] && [ -f "$latest_run/metadata.json" ]; then
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  tmp_file="$(mktemp)"
  sed -e "s/\"finished_at\": \"\"/\"finished_at\": \"$finished_at\"/" \
      -e 's/"status": "started"/"status": "stopped"/' \
      "$latest_run/metadata.json" > "$tmp_file"
  mv "$tmp_file" "$latest_run/metadata.json"
fi
