FROM ubuntu:22.04@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982

ARG DEBIAN_FRONTEND=noninteractive
ARG LAIN5G_VERSION=1.0.0-rc.1
ARG OPEN5GS_VERSION=v2.7.5
ARG OPEN5GS_COMMIT=7dfd9a39649700c24c22f1978ed7a35541a72cca

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        bison \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        flex \
        git \
        iproute2 \
        iptables \
        iputils-ping \
        libbson-dev \
        libcurl4-gnutls-dev \
        libgcrypt20-dev \
        libgnutls28-dev \
        libidn11-dev \
        libmicrohttpd-dev \
        libmongoc-dev \
        libnghttp2-dev \
        libssl-dev \
        libsctp-dev \
        libtalloc-dev \
        libyaml-dev \
        meson \
        netbase \
        ninja-build \
        pkg-config \
        tcpdump \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${OPEN5GS_VERSION}" https://github.com/open5gs/open5gs.git open5gs \
    && cd open5gs \
    && git fetch --depth 1 origin "${OPEN5GS_COMMIT}" \
    && git checkout --detach "${OPEN5GS_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${OPEN5GS_COMMIT}" \
    && meson setup build --prefix=/usr/local \
    && ninja -C build \
    && ninja -C build install \
    && ldconfig \
    && for bin in open5gs-nrfd open5gs-amfd open5gs-smfd open5gs-upfd open5gs-ausfd open5gs-udmd open5gs-udrd open5gs-pcfd; do \
        command -v "$bin"; \
    done \
    && rm -rf /opt/open5gs/.git /opt/open5gs/build

COPY entrypoint.sh /usr/local/bin/lain5g-open5gs-entrypoint
RUN mkdir -p /var/log/open5gs \
    && chmod +x /usr/local/bin/lain5g-open5gs-entrypoint

ENTRYPOINT ["lain5g-open5gs-entrypoint"]
