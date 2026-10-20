#!/usr/bin/env bash
set -euo pipefail
if [ "${LAIN5G_DRY_RUN:-false}" = true ]; then
  echo "DRY RUN: 4G LTE USRP hardware-check plan; no device, network, UHD, Docker, or file access was performed"
  exit 0
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
env_file="$script_dir/../../common/.env"
[ -f "$env_file" ] && set -a && source "$env_file" && set +a
addr="${USRP_ADDR:-192.168.10.2}"
image="${LAIN5G_UHD_IMAGE:-lain5g-lab/srsran4g-uhd:local}"
status=PASS
check(){ printf '%-22s %s %s\n' "$1" "$2" "$3"; [ "$2" = FAIL ] && status=FAIL; return 0; }
route="$(ip -4 route get "$addr" 2>/dev/null | head -n1 || true)"
iface="$(awk '{for(i=1;i<=NF;i++) if($i=="dev") {print $(i+1); exit}}' <<< "$route")"
source_ip="$(awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}' <<< "$route")"
if [ -n "$iface" ] && [ "$iface" != lo ] && [ -n "$source_ip" ] && ! awk '{for(i=1;i<=NF;i++) if($i=="via") found=1} END {exit !found}' <<< "$route"; then
  check ethernet_link PASS "route to $addr uses $iface ($source_ip)"
else
  check ethernet_link FAIL "no directly connected host IPv4 route to configured radio address $addr"
fi
ping -c 1 -W 1 "$addr" >/dev/null 2>&1 && check usrp_ping PASS "USRP responds at $addr" || { check usrp_ping FAIL "USRP did not respond at $addr"; }
if command -v uhd_find_devices >/dev/null 2>&1; then
  out="$(uhd_find_devices --args "addr=$addr" 2>&1 || true)"
elif docker image inspect "$image" >/dev/null 2>&1; then
  out="$(docker run --rm --network host "$image" uhd_find_devices --args "addr=$addr" 2>&1 || true)"
else
  out=""
  check uhd_find_devices FAIL "uhd_find_devices missing and image $image not found"
fi
if [ -n "$out" ]; then
  printf '%s\n' "$out" > /tmp/lain5g-uhd-find-devices.log
  if printf '%s\n' "$out" | grep -Eiq 'product: X300|type: x300|addr:'; then
    check uhd_find_devices PASS "compatible USRP found"
  else
    check uhd_find_devices FAIL "UHD did not report a compatible USRP"
  fi
  serial="$(printf '%s\n' "$out" | sed -n 's/.*serial: *//Ip' | head -n1)"
  [ -n "$serial" ] && echo "serial_redacted=${serial:0:3}***${serial: -2}"
fi
echo "status=$status"
test "$status" != FAIL
