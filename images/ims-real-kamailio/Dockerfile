FROM debian:bookworm-slim@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818

ARG DEBIAN_FRONTEND=noninteractive
ARG LAIN5G_VERSION=1.1.6
ARG KAMAILIO_VERSION=6.0.8
ARG KAMAILIO_COMMIT=73c93991e31cea52304b96e7bc5b3d1c9f3caa33

RUN apt-get update && apt-get install -y --no-install-recommends \
      bison build-essential ca-certificates flex git libcurl4-gnutls-dev \
      libevent-dev libexpat1-dev libjansson-dev libmariadb-dev libmnl-dev \
      libnghttp2-dev libpcre3-dev libssl-dev libsctp-dev libsystemd-dev \
      libunistring-dev libuuid1 libxml2-dev libxmlrpc-core-c3-dev pkg-config \
      uuid-dev zlib1g-dev mariadb-client iproute2 iptables \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/build
RUN git clone --depth 1 --branch "${KAMAILIO_VERSION}" https://github.com/kamailio/kamailio.git kamailio \
    && cd kamailio \
    && git fetch --depth 1 origin "${KAMAILIO_COMMIT}" \
    && git checkout --detach "${KAMAILIO_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${KAMAILIO_COMMIT}" \
    && cd src \
    && make cfg PREFIX=/usr/local include_modules="auth cdp cdp_avp cfg_rpc corex ctl db_cluster db_mysql debugger dispatcher enum htable http_client ims_auth ims_charging ims_dialog ims_icscf ims_ipsec_pcscf ims_isc ims_qos ims_registrar_pcscf ims_registrar_scscf ims_usrloc_pcscf ims_usrloc_scscf jansson jsonrpcs kex maxfwd nathelper nghttp2 path pike presence pua pv registrar rr rtpengine sanity sctp sdpops siptrace siputils sl sqlops statistics textops textopsx tls tm tmx uac usrloc uuid websocket xhttp xlog xmlrpc" \
    && make all -j"$(nproc)" \
    && make install \
    && mkdir -p /usr/local/src/kamailio/utils/kamctl \
    && cp -a ../utils/kamctl/mysql /usr/local/src/kamailio/utils/kamctl/ \
    && /usr/local/sbin/kamailio -v \
    && cd / \
    && rm -rf /tmp/build

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="OpenLain5G Real IMS Kamailio" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G" \
      org.opencontainers.image.licenses="MIT AND GPL-2.0-only AND BSD-2-Clause" \
      org.opencontainers.image.description="OpenLain5G-built Kamailio with IMS Diameter modules and packaged P/I/S-CSCF configurations"

COPY roles/ /mnt/
COPY runtime/kamailio-ims-entrypoint.sh /usr/local/bin/kamailio-ims-entrypoint

# The inherited reference config loaded rtpping.so, but did not use it; this
# module is absent from the pinned Kamailio release, so omit that load only.
RUN sed -i '/loadmodule "rtpping.so"/d' /mnt/pcscf/kamailio_pcscf.cfg \
    && chmod 0755 /usr/local/bin/kamailio-ims-entrypoint

ENTRYPOINT ["/usr/local/bin/kamailio-ims-entrypoint"]
