FROM ubuntu:22.04@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982

ARG DEBIAN_FRONTEND=noninteractive
ARG LAIN5G_VERSION=1.0.0-rc.1
ARG SRSRAN_4G_VERSION=release_23_11
ARG SRSRAN_4G_COMMIT=eea87b1d893ae58e0b08bc381730c502024ae71f

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      bash build-essential ca-certificates cmake git iproute2 iputils-ping \
      libboost-program-options-dev libconfig++-dev libfftw3-dev libmbedtls-dev \
      libsctp-dev libzmq3-dev pkg-config python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${SRSRAN_4G_VERSION}" https://github.com/srsran/srsRAN_4G.git srsran4g \
    && cd srsran4g \
    && git fetch --depth 1 origin "${SRSRAN_4G_COMMIT}" \
    && git checkout --detach "${SRSRAN_4G_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${SRSRAN_4G_COMMIT}" \
    && cmake -S . -B build -DENABLE_ZEROMQ=ON -DENABLE_UHD=OFF -DENABLE_GUI=OFF \
    && cmake --build build -j"$(nproc)" \
    && cmake --install build \
    && ldconfig \
    && command -v srsenb \
    && command -v srsue \
    && rm -rf /opt/srsran4g/.git /opt/srsran4g/build

COPY entrypoint.sh /usr/local/bin/lain5g-srsran4g-sim-entrypoint
RUN chmod +x /usr/local/bin/lain5g-srsran4g-sim-entrypoint

ENTRYPOINT ["lain5g-srsran4g-sim-entrypoint"]
