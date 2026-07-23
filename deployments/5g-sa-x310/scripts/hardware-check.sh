#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 5G SA X310 hardware-check plan; no device, network, UHD, Docker, or file access was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "$script_dir/.." && pwd)"
env_file="${1:-$scenario_dir/.env}"
[ -f "$env_file" ] && set -a && source "$env_file" && set +a
addr="${USRP_ADDR:-192.168.10.2}"
usrp_type="${USRP_TYPE:-x300}"
image="${LAIN5G_SRSRANPROJECT_UHD_IMAGE:-lain5g-lab/srsranproject-uhd:local}"
status=PASS

check(){ printf '%-24s %s %s\n' "$1" "$2" "$3"; [ "$2" = FAIL ] && status=FAIL; return 0; }
redact(){ sed -E 's/([Ss]erial:[[:space:]]*)([[:alnum:]]{3})[[:alnum:]]*([[:alnum:]]{2})/\1\2***\3/g; s/(serial[[:space:]]*=[: ]?)([[:alnum:]]{3})[[:alnum:]]*([[:alnum:]]{2})/\1\2***\3/Ig; s/(mac-addr[0-9]*:[[:space:]]*)[0-9a-fA-F:]+/\1**:**:**:**:**:**/g; s/(Device DNA:[[:space:]]*)[0-9a-fA-F]+/\1<redacted>/g'; }
run_uhd(){
  local tool="$1"; shift
  if command -v "$tool" >/dev/null 2>&1 && uhd_config_info --version 2>/dev/null | grep -Fq '4.10.0'; then
    "$tool" "$@"
  elif docker image inspect "$image" >/dev/null 2>&1; then
    docker run --rm --network host "$image" "$tool" "$@"
  else
    return 127
  fi
}

if ip -4 -o addr show | grep -Eq '192\.168\.(10|30)\.'; then
  host_ip="$(ip -4 -o addr show | awk '/192\.168\.(10|30)\./ {print $4; exit}')"
  check ethernet_link PASS "compatible host subnet: $host_ip"
else
  check ethernet_link WARNING "no 192.168.10/30 host address found"
fi

ping -c 1 -W 1 "$addr" >/dev/null 2>&1 && check x310_ping PASS "X310 responds at $addr" || check x310_ping FAIL "X310 did not respond at $addr"

version_out="$(run_uhd uhd_config_info --version 2>&1 || true)"
if printf '%s\n' "$version_out" | grep -Fq '4.10.0'; then check uhd_version PASS "$(printf '%s\n' "$version_out" | head -n1)"; else check uhd_version FAIL "UHD 4.10.0 not available"; fi

find_out="$(run_uhd uhd_find_devices --args "type=$usrp_type,addr=$addr" 2>&1 || true)"
printf '%s\n' "$find_out" | redact > /tmp/lain5g-5g-x310-find-devices.log
printf '%s\n' "$find_out" | grep -Eiq 'type: x300|product: X300|X310|addr:' && check uhd_find_devices PASS "X300/X310 device found" || check uhd_find_devices FAIL "X300/X310 device not found"
serial="$(printf '%s\n' "$find_out" | sed -n 's/.*serial: *//Ip' | head -n1)"
[ -n "$serial" ] && printf 'serial_redacted=%s***%s\n' "${serial:0:3}" "${serial: -2}"

probe_out="$(run_uhd uhd_usrp_probe --args "type=$usrp_type,addr=$addr" 2>&1 || true)"
printf '%s\n' "$probe_out" | redact > /tmp/lain5g-5g-x310-usrp-probe.log
printf '%s\n' "$probe_out" | grep -Eiq 'Device: X-Series Device|Mboard: X3[01]0|product: X3[01]0|type: x300' && check model PASS "X310/X300 family probed" || check model FAIL "expected X310/X300 markers missing"
printf '%s\n' "$probe_out" | grep -Eiq 'FPGA Version|FPGA git hash|fpga' && check fpga_version PASS "FPGA version reported" || check fpga_version WARNING "FPGA version not parsed"
printf '%s\n' "$probe_out" | grep -Eiq 'Dboard|Daughterboard|RX.*Subdev|TX.*Subdev' && check daughterboards PASS "daughterboard information reported" || check daughterboards WARNING "daughterboards not parsed"
printf '%s\n' "$probe_out" | grep -Eiq 'Clock|clock|internal' && check clock_source PASS "clock information available" || check clock_source WARNING "clock information not parsed"

echo "status=$status"
test "$status" != FAIL
