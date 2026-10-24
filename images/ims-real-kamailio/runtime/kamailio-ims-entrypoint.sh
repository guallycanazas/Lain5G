#!/usr/bin/env bash
set -euo pipefail

component="${COMPONENT_NAME:-}"
case "$component" in
  icscf|pcscf|scscf) ;;
  *) echo "OpenLain5G IMS Kamailio image: unsupported COMPONENT_NAME" >&2; exit 64 ;;
esac

role_script="/mnt/${component}/${component}_init.sh"
if [[ ! -x "$role_script" ]]; then
  echo "OpenLain5G IMS Kamailio image: role script is missing or not executable" >&2
  exit 66
fi

exec "$role_script" "$@"
