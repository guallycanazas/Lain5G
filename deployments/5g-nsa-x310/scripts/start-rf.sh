#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  printf '%s\n' \
    "DRY RUN: guarded 5G NSA RF start plan" \
    "DRY RUN: authorization and safety checks would precede a time-limited RF service request" \
    "DRY RUN: no RF, UHD, Docker, network, volume, configuration, file, or marker action was executed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
repo_dir="$(cd "$scenario_dir/../.." && pwd)"
env_file="$scenario_dir/.env"; [ -f "$env_file" ] || env_file="$scenario_dir/.env.example"
manifest="$scenario_dir/rf/safety-manifest.yaml"
[ "${LAIN5G_ALLOW_5G_NSA_RF_START:-false}" = true ] || { echo "NSA RF start refused: set LAIN5G_ALLOW_5G_NSA_RF_START=true" >&2; exit 2; }
command -v flock >/dev/null 2>&1 || { echo "NSA RF start refused: flock is required" >&2; exit 2; }
exec 9<"$repo_dir"
flock -n -x 9 || { echo "NSA RF start refused: another RF start is in progress" >&2; exit 2; }
for marker in "$repo_dir/deployments/4g-volte/x310/.rf-active" "$repo_dir/deployments/5g-sa-x310/.rf-active" "$repo_dir/deployments/5g-nsa-x310/.rf-active"; do
  [ ! -f "$marker" ] || { echo "NSA RF start refused: another RF session is active" >&2; exit 2; }
done
REQUIRE_RF_READY=true "$script_dir/preflight.sh"
# Let the UHD probe release the X310 management channel before srsENB opens it.
sleep 5
maximum_duration="$(sed -n 's/^maximum_duration_seconds:[[:space:]]*//p' "$manifest" | head -n1)"
duration="${LAIN5G_RF_DURATION_SECONDS:-$maximum_duration}"
[[ "$duration" =~ ^[0-9]+$ ]] && [ "$duration" -ge 1 ] && [ "$duration" -le "$maximum_duration" ] || { echo "NSA RF start refused: duration must be 1..${maximum_duration} seconds" >&2; exit 2; }
run_id="${LAIN5G_RUN_ID:-run-$(date -u +%Y%m%d-%H%M%S)}"
run_dir="$repo_dir/runs/$run_id"
mkdir -p "$run_dir/logs"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'started_at=%s\nrun_id=%s\nduration_seconds=%s\noperator_note=%s\n' "$started_at" "$run_id" "$duration" "${LAIN5G_RF_OPERATOR_NOTE:-not supplied}" >"$scenario_dir/.rf-active"
session_file="$run_dir/rf-session.json"
printf '{"scenario":"5g-nsa-x310","run_id":"%s","status":"starting","started_at":"%s","duration_seconds":%s}\n' "$run_id" "$started_at" "$duration" > "$session_file"
if ! (cd "$scenario_dir" && LAIN5G_RF_DURATION_SECONDS="$duration" docker compose --env-file "$env_file" -f docker-compose.yml --profile rf up -d enb-nsa-x310); then
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '{"scenario":"5g-nsa-x310","run_id":"%s","status":"failed","started_at":"%s","finished_at":"%s","duration_seconds":%s,"failure":"Compose could not start the guarded eNB service"}\n' "$run_id" "$started_at" "$finished_at" "$duration" > "$session_file"
  rm -f "$scenario_dir/.rf-active"
  echo "NSA RF start failed: Compose could not start the eNB service" >&2
  exit 1
fi
sleep 3
if [ "$(docker inspect -f '{{.State.Running}}' lain5g-lab-5g-nsa-x310-enb 2>/dev/null || true)" != true ]; then
  (cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf logs --no-color --since "$started_at" enb-nsa-x310 >"$run_dir/logs/enb-nsa-x310.log" 2>/dev/null || true)
  exit_code="$(docker inspect -f '{{.State.ExitCode}}' lain5g-lab-5g-nsa-x310-enb 2>/dev/null || printf 'unknown')"
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if grep -Eiq 'RFNOC::GRAPH|RfnocError|RFNoC protocol mismatch|Failure to create rfnoc_graph|uhd_init failed|Management operation failed|Incorrect number of operations' "$run_dir/logs/enb-nsa-x310.log"; then
    failure='RFNoC graph initialization failed; check UHD/FPGA compatibility and X310 management-link state'
    echo "NSA RF start failed: RFNoC graph initialization failed (container exit ${exit_code}); check that the FPGA image is compatible with UHD 4.10 in the selected srsRAN image and inspect the X310 control-link/network state. Session log: runs/${run_id}/logs/enb-nsa-x310.log" >&2
  else
    failure='eNB exited during UHD initialization'
    echo "NSA RF start failed: eNB exited during UHD initialization (container exit ${exit_code}); session log: runs/${run_id}/logs/enb-nsa-x310.log" >&2
  fi
  failure_json="$(printf '%s' "$failure" | sed 's/\\/\\\\/g; s/"/\\"/g')"
  printf '{"scenario":"5g-nsa-x310","run_id":"%s","status":"failed","started_at":"%s","finished_at":"%s","duration_seconds":%s,"container_exit_code":"%s","failure":"%s"}\n' "$run_id" "$started_at" "$finished_at" "$duration" "$exit_code" "$failure_json" > "$session_file"
  rm -f "$scenario_dir/.rf-active"
  tail -n 45 "$run_dir/logs/enb-nsa-x310.log" >&2 || true
  exit 1
fi
printf '{"scenario":"5g-nsa-x310","run_id":"%s","status":"running","started_at":"%s","duration_seconds":%s}\n' "$run_id" "$started_at" "$duration" > "$session_file"
(
  exec 9>&-
  while [ "$(docker inspect -f '{{.State.Running}}' lain5g-lab-5g-nsa-x310-enb 2>/dev/null || true)" = true ]; do sleep 2; done
  (cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf logs --no-color --since "$started_at" enb-nsa-x310 >"$run_dir/logs/enb-nsa-x310.log" 2>/dev/null || true)
  (cd "$scenario_dir" && docker compose --env-file "$env_file" -f docker-compose.yml --profile rf stop enb-nsa-x310 >/dev/null 2>&1 || true)
  exit_code="$(docker inspect -f '{{.State.ExitCode}}' lain5g-lab-5g-nsa-x310-enb 2>/dev/null || printf 'unknown')"
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  started_epoch="$(date -u -d "$started_at" +%s 2>/dev/null || printf '0')"
  finished_epoch="$(date -u +%s)"
  elapsed=$((finished_epoch - started_epoch))
  if [ "$exit_code" = 124 ] || { [ "$exit_code" = 143 ] && [ "$elapsed" -ge "$((duration - 3))" ]; }; then
    session_status=auto_stopped
    failure=null
  elif [ "$exit_code" = 143 ] && ! grep -Fxq "run_id=$run_id" "$scenario_dir/.rf-active" 2>/dev/null; then
    session_status=stopped
    failure=null
  else
    session_status=failed
    failure='"eNB exited before the requested auto-stop duration"'
  fi
  printf '{"scenario":"5g-nsa-x310","run_id":"%s","status":"%s","started_at":"%s","finished_at":"%s","duration_seconds":%s,"elapsed_seconds":%s,"container_exit_code":"%s","failure":%s}\n' \
    "$run_id" "$session_status" "$started_at" "$finished_at" "$duration" "$elapsed" "$exit_code" "$failure" > "$session_file"
  if grep -Fxq "run_id=$run_id" "$scenario_dir/.rf-active" 2>/dev/null; then rm -f "$scenario_dir/.rf-active"; fi
) </dev/null >/dev/null 2>&1 &
echo "NSA RF session $run_id started; container auto-stop is enforced after ${duration}s"
echo "Emergency stop remains available through the app"
