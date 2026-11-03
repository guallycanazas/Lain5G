#!/usr/bin/env bash
set -euo pipefail
scenario_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../../.." && pwd)"
latest_run=""
for metadata in "$repo_dir"/runs/run-*/metadata.json; do
  [ -f "$metadata" ] || continue
  grep -Eq '"scenario"[[:space:]]*:[[:space:]]*"4g-volte-sim"' "$metadata" && latest_run="$(dirname "$metadata")"
done

compose(){ (cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml "$@"); }
if [ "${LAIN5G_DRY_RUN:-false}" = "true" ]; then
  echo "DRY RUN: archive 4G VoLTE simulation logs and stop services; preserve MongoDB data"
  exit 0
fi

if [ -n "$latest_run" ]; then
  mkdir -p "$latest_run/logs"
  compose logs --no-color --tail 1000 > "$latest_run/logs/docker-compose.log" 2>/dev/null || true
fi

compose stop

if [ -n "$latest_run" ]; then
  python3 - "$latest_run/metadata.json" <<'PY'
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

metadata_path = Path(sys.argv[1])
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
metadata["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
if metadata.get("status") == "started":
    metadata["status"] = "stopped"
with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=metadata_path.parent, delete=False) as handle:
    temporary_path = Path(handle.name)
    json.dump(metadata, handle, indent=2)
    handle.write("\n")
os.replace(temporary_path, metadata_path)
PY
fi
