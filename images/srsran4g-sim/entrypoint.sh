#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ge 2 ] && [ "$1" = "srsue" ] && [ "$2" = "/etc/srsran/ue.conf" ]; then
  runtime_conf=/tmp/lain5g-srsue.conf
  cp /etc/srsran/ue.conf "$runtime_conf"
  if [ -n "${SUBSCRIBER_IMSI:-}" ]; then
    perl -0pi -e 's/^imsi = .*/imsi = $ENV{SUBSCRIBER_IMSI}/m' "$runtime_conf"
  fi
  if [ -n "${SUBSCRIBER_KEY:-}" ]; then
    perl -0pi -e 's/^k = .*/k = $ENV{SUBSCRIBER_KEY}/m' "$runtime_conf"
  fi
  if [ -n "${SUBSCRIBER_OPC:-}" ]; then
    perl -0pi -e 's/^opc = .*/opc = $ENV{SUBSCRIBER_OPC}/m' "$runtime_conf"
  fi
  exec srsue "$runtime_conf"
fi

exec "$@"
