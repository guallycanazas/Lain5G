#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: <open5gs-binary> -c <config-file>" >&2
  exit 64
fi

if [ -n "${FD_HSS_CONNECT_TO:-}" ] && [ -f /usr/local/etc/freeDiameter/mme.conf ]; then
  FD_CONNECT_TO="$FD_HSS_CONNECT_TO" perl -0pi -e 's/ConnectPeer = "hss\.localdomain" \{ ConnectTo = "[^"]+"; No_TLS; \};/q(ConnectPeer = "hss.localdomain" { ConnectTo = ") . $ENV{FD_CONNECT_TO} . q("; No_TLS; };)/ge' /usr/local/etc/freeDiameter/mme.conf
fi

if [ -n "${FD_MME_CONNECT_TO:-}" ] && [ -f /usr/local/etc/freeDiameter/hss.conf ]; then
  FD_CONNECT_TO="$FD_MME_CONNECT_TO" perl -0pi -e 's/ConnectPeer = "mme\.localdomain" \{ ConnectTo = "[^"]+"; No_TLS; \};/q(ConnectPeer = "mme.localdomain" { ConnectTo = ") . $ENV{FD_CONNECT_TO} . q("; No_TLS; };)/ge' /usr/local/etc/freeDiameter/hss.conf
fi

if [ -n "${FD_PCRF_CONNECT_TO:-}" ] && [ -f /usr/local/etc/freeDiameter/smf.conf ]; then
  FD_CONNECT_TO="$FD_PCRF_CONNECT_TO" perl -0pi -e 's/ConnectPeer = "pcrf\.localdomain" \{ ConnectTo = "[^"]+"; No_TLS; \};/q(ConnectPeer = "pcrf.localdomain" { ConnectTo = ") . $ENV{FD_CONNECT_TO} . q("; No_TLS; };)/ge' /usr/local/etc/freeDiameter/smf.conf
fi

if [ -n "${FD_SMF_CONNECT_TO:-}" ] && [ -f /usr/local/etc/freeDiameter/pcrf.conf ]; then
  FD_CONNECT_TO="$FD_SMF_CONNECT_TO" perl -0pi -e 's/ConnectPeer = "smf\.localdomain" \{ ConnectTo = "[^"]+"; No_TLS; \};/q(ConnectPeer = "smf.localdomain" { ConnectTo = ") . $ENV{FD_CONNECT_TO} . q("; No_TLS; };)/ge' /usr/local/etc/freeDiameter/pcrf.conf
fi

if [ -n "${FD_LISTEN_ON:-}" ]; then
  for fd_conf in /usr/local/etc/freeDiameter/*.conf; do
    [ -f "$fd_conf" ] || continue
    perl -0pi -e 's/\\nListenOn = "[^"]+";//g' "$fd_conf"
    printf '\nListenOn = "%s";\n' "$FD_LISTEN_ON" >> "$fd_conf"
  done
fi

if [ "$(basename "$1")" = "open5gs-upfd" ]; then
  ue_subnet="${UE_SUBNET:-10.45.0.0/16}"
  ue_gateway="${UE_GATEWAY:-10.45.0.1}"
  ue_prefix="${ue_subnet#*/}"

  if [ "$ue_prefix" = "$ue_subnet" ]; then
    ue_prefix="16"
  fi

  ip tuntap add name ogstun mode tun 2>/dev/null || true
  ip addr replace "${ue_gateway}/${ue_prefix}" dev ogstun
  ip link set ogstun up
  iptables -t nat -C POSTROUTING -s "$ue_subnet" ! -o ogstun -j MASQUERADE 2>/dev/null \
    || iptables -t nat -A POSTROUTING -s "$ue_subnet" ! -o ogstun -j MASQUERADE

  if [ -n "${UE_IMS_SUBNET:-}" ]; then
    ims_subnet="$UE_IMS_SUBNET"
    ims_gateway="${UE_IMS_GATEWAY:-10.61.0.1}"
    ims_prefix="${ims_subnet#*/}"
    if [ "$ims_prefix" = "$ims_subnet" ]; then
      ims_prefix="16"
    fi
    ip tuntap add name ogstun2 mode tun 2>/dev/null || true
    ip addr replace "${ims_gateway}/${ims_prefix}" dev ogstun2
    ip link set ogstun2 up
    iptables -t nat -C POSTROUTING -s "$ims_subnet" ! -o ogstun2 -j MASQUERADE 2>/dev/null \
      || iptables -t nat -A POSTROUTING -s "$ims_subnet" ! -o ogstun2 -j MASQUERADE
  fi
fi

exec "$@"
