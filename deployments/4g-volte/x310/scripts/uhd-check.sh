#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 4G LTE X310 UHD-check plan; no device, network, UHD, Docker, or file access was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
env_file="$script_dir/../../common/.env"
[ -f "$env_file" ] && set -a && source "$env_file" && set +a
addr="${USRP_ADDR:-192.168.10.2}"
image="${LAIN5G_UHD_IMAGE:-lain5g-lab/srsran4g-uhd:local}"
log="${LAIN5G_UHD_LOG:-/tmp/lain5g-uhd-probe.log}"
raw_log="${log}.raw"
redact(){ sed -E 's/([Ss]erial:[[:space:]]*)([[:alnum:]]{3})[[:alnum:]]*([[:alnum:]]{2})/\1\2***\3/g; s/(mac-addr[0-9]*:[[:space:]]*)[0-9a-fA-F:]+/\1**:**:**:**:**:**/g; s/(Device DNA:[[:space:]]*)[0-9a-fA-F]+/\1<redacted>/g'; }
if docker image inspect "$image" >/dev/null 2>&1; then
  cmd=(docker run --rm --network host "$image" uhd_usrp_probe --args "addr=$addr")
elif command -v uhd_usrp_probe >/dev/null 2>&1; then
  cmd=(uhd_usrp_probe --args "addr=$addr")
else
  echo "uhd_available FAIL uhd_usrp_probe missing and image $image not found"
  exit 1
fi
probe_ok=false
for attempt in 1 2 3; do
  if "${cmd[@]}" >"$raw_log" 2>&1; then
    probe_ok=true
    [ "$attempt" -eq 1 ] || echo "uhd_probe INFO probe succeeded on retry $attempt"
    break
  fi
  echo "uhd_probe WARNING attempt $attempt/3 failed"
  if [ "$attempt" -lt 3 ]; then sleep 2; fi
done
if [ "$probe_ok" != true ]; then
  redact <"$raw_log" | tee "$log"
  echo "uhd_probe FAIL probe failed after 3 attempts"
  exit 1
fi
redact <"$raw_log" >"$log"
cat "$log"
grep -Eiq 'compat number mismatch|incompatible|Expected FPGA' "$log" && { echo "uhd_fpga_compatible FAIL incompatible FPGA/UHD"; exit 1; }
grep -Eiq 'Device: X-Series Device|Mboard: X300|product: X300|type: x300' "$log" && echo "uhd_probe PASS X-series device probed" || { echo "uhd_probe FAIL expected X300/X310 markers missing"; exit 1; }
grep -Eiq 'FPGA Version|fpga:' "$log" && echo "uhd_fpga_compatible PASS FPGA reported by successful UHD probe" || { echo "uhd_fpga_compatible FAIL FPGA details missing"; exit 1; }
