#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
latest_run=""
for metadata in "$repo_dir"/runs/run-*/metadata.json; do
  [ -f "$metadata" ] || continue
  grep -Eq '"scenario"[[:space:]]*:[[:space:]]*"4g-lte-sim"' "$metadata" && latest_run="$(dirname "$metadata")"
done

compose(){ (cd "$scenario_dir" && docker compose --env-file ../4g-volte/common/.env -f docker-compose.yml "$@"); }
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: archive LTE simulation logs, stop services, remove eNB/UE containers, preserve MongoDB data"
  exit 0
fi

# Preserve diagnostic history with the run before removing the RAN containers.
# Recreating eNB/UE on the next start resets their stopped network namespaces,
# including any stale srsUE TUN interface that can block a repeated attach.
if [ -n "$latest_run" ]; then
  mkdir -p "$latest_run/logs"
  compose logs --no-color > "$latest_run/logs/docker-compose.log" 2>/dev/null || true
  for service in mongo mme hss sgwc sgwu pgwc pgwu pcrf enb ue; do
    compose logs --no-color "$service" > "$latest_run/logs/$service.log" 2>/dev/null || true
  done
fi

compose stop
compose rm --force enb ue >/dev/null

if [ -n "$latest_run" ]; then
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  tmp_file="$(mktemp)"
  sed -E -e "s/\"finished_at\"[[:space:]]*:[[:space:]]*\"\"/\"finished_at\":\"$finished_at\"/" \
      -e 's/"status"[[:space:]]*:[[:space:]]*"started"/"status":"stopped"/' \
      "$latest_run/metadata.json" > "$tmp_file"
  mv "$tmp_file" "$latest_run/metadata.json"
fi
