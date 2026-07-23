FROM ubuntu:22.04@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982

ARG DEBIAN_FRONTEND=noninteractive
ARG LAIN5G_VERSION=1.0.0-rc.1
ARG UERANSIM_VERSION=v3.2.6
ARG UERANSIM_COMMIT=384636f4fcf46b8c86109790ff3e2cd242b53556

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        cmake \
        git \
        iproute2 \
        iputils-ping \
        lksctp-tools \
        libsctp-dev \
        make \
        net-tools \
        tcpdump \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${UERANSIM_VERSION}" https://github.com/aligungr/UERANSIM.git ueransim \
    && cd ueransim \
    && git fetch --depth 1 origin "${UERANSIM_COMMIT}" \
    && git checkout --detach "${UERANSIM_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${UERANSIM_COMMIT}" \
    && make -j"$(nproc)" \
    && install -m 0755 build/nr-gnb /usr/local/bin/nr-gnb \
    && install -m 0755 build/nr-ue /usr/local/bin/nr-ue \
    && command -v nr-gnb \
    && command -v nr-ue \
    && (nr-gnb --version >/dev/null 2>&1 || true) \
    && (nr-ue --version >/dev/null 2>&1 || true) \
    && rm -rf /opt/ueransim/.git

COPY entrypoint.sh /usr/local/bin/lain5g-ueransim-entrypoint
RUN chmod +x /usr/local/bin/lain5g-ueransim-entrypoint

ENTRYPOINT ["lain5g-ueransim-entrypoint"]
