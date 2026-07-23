#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  printf '%s\n' \
    "DRY RUN: guarded 4G LTE RF start plan" \
    "DRY RUN: authorization and safety checks would precede a time-limited RF service request" \
    "DRY RUN: no RF, UHD, Docker, network, volume, configuration, file, or marker action was executed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../../.." && pwd)"
manifest="$scenario_dir/rf/safety-manifest.yaml"
if [ "${LAIN5G_ALLOW_RF_START:-false}" != "true" ]; then echo "RF start refused: set LAIN5G_ALLOW_RF_START=true" >&2; exit 2; fi
if [ -f "$scenario_dir/.rf-active" ]; then echo "RF session already active" >&2; exit 2; fi
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"
mkdir -p "$run_dir/logs"
REQUIRE_RF_READY=true LAIN5G_RUN_ID="$run_id" "$script_dir/preflight.sh"
# Let the UHD probe release the X310 management channel before srsENB opens it.
sleep 5
maximum_duration="$(sed -n 's/^maximum_duration_seconds:[[:space:]]*//p' "$manifest" | head -n1)"
duration="${LAIN5G_RF_DURATION_SECONDS:-$maximum_duration}"
[[ "$duration" =~ ^[0-9]+$ ]] && [ "$duration" -gt 0 ] && [ "$duration" -le "$maximum_duration" ] || { echo "RF start refused: duration must be 1..${maximum_duration} seconds" >&2; exit 2; }

if command -v cpupower >/dev/null 2>&1; then
  if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    cpupower frequency-set -g performance >/dev/null 2>&1 || echo "WARNING: could not set CPU governor to performance" >&2
  elif sudo -n true 2>/dev/null; then
    sudo -n cpupower frequency-set -g performance >/dev/null 2>&1 || echo "WARNING: could not set CPU governor to performance" >&2
  else
    echo "WARNING: sudo is required to set CPU governor to performance" >&2
  fi
else
  echo "WARNING: cpupower not found; CPU governor was not changed" >&2
fi

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'started_at=%s\nrun_id=%s\nduration_seconds=%s\noperator_note=%s\n' "$started_at" "$run_id" "$duration" "${LAIN5G_RF_OPERATOR_NOTE:-not supplied}" > "$scenario_dir/.rf-active"
(cd "$scenario_dir" && LAIN5G_RF_DURATION_SECONDS="$duration" docker compose --env-file ../common/.env -f docker-compose.yml --profile rf up -d enb-x310)
sleep 3
if [ "$(docker inspect -f '{{.State.Running}}' lain5g-lab-4g-lte-x310-enb 2>/dev/null || true)" != true ]; then
  rm -f "$scenario_dir/.rf-active"
  echo "RF start failed: eNB exited during UHD initialization" >&2
  exit 1
fi
(
  while [ "$(docker inspect -f '{{.State.Running}}' lain5g-lab-4g-lte-x310-enb 2>/dev/null || true)" = true ]; do sleep 2; done
  (cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml --profile rf logs --no-color --since "$started_at" enb-x310 >"$run_dir/logs/enb-x310.log" 2>/dev/null || true)
  if grep -Fxq "run_id=$run_id" "$scenario_dir/.rf-active" 2>/dev/null; then
    (cd "$scenario_dir" && docker compose --env-file ../common/.env -f docker-compose.yml --profile rf stop enb-x310 >/dev/null 2>&1 || true)
    rm -f "$scenario_dir/.rf-active"
  fi
) </dev/null >/dev/null 2>&1 &
echo "RF session $run_id started; container auto-stop is enforced after ${duration}s"
echo "Emergency stop remains available through the app"
