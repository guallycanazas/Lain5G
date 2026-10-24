#!/usr/bin/env bash
set -euo pipefail

component="${COMPONENT_NAME:-}"
case "$component" in
  amf|ausf|bsf|hss|mme|nrf|nssf|pcf|pcrf|scp|sgwc|sgwu|smf|udm|udr|upf) ;;
  *) echo "OpenLain5G IMS image: unsupported COMPONENT_NAME" >&2; exit 64 ;;
esac

role_script="/mnt/${component}/${component}_init.sh"
if [[ ! -x "$role_script" ]]; then
  echo "OpenLain5G IMS image: role script is missing or not executable" >&2
  exit 66
fi

cd /open5gs
exec "$role_script" "$@"
