FROM ubuntu:22.04@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982

ARG DEBIAN_FRONTEND=noninteractive
ARG LAIN5G_VERSION=1.0.0-rc.1
ARG SRSRAN_4G_VERSION=release_23_11
ARG SRSRAN_4G_COMMIT=eea87b1d893ae58e0b08bc381730c502024ae71f
ARG UHD_VERSION=v4.10.0.0
ARG UHD_COMMIT=2af4ddb96219a99d2300804830e0971f79557b23

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      bash build-essential ca-certificates cmake git iproute2 iputils-ping \
      libboost-all-dev libconfig++-dev libfftw3-dev libmbedtls-dev libsctp-dev \
      libusb-1.0-0-dev pkg-config python3 python3-mako python3-numpy python3-requests python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${UHD_VERSION}" https://github.com/EttusResearch/uhd.git uhd \
    && git -C uhd fetch --depth 1 origin "${UHD_COMMIT}" \
    && git -C uhd checkout --detach "${UHD_COMMIT}" \
    && test "$(git -C uhd rev-parse HEAD)" = "${UHD_COMMIT}" \
    && cmake -S uhd/host -B uhd/host/build -DENABLE_TESTS=OFF -DENABLE_EXAMPLES=OFF \
    && cmake --build uhd/host/build -j"$(nproc)" \
    && cmake --install uhd/host/build \
    && ldconfig \
    && command -v uhd_find_devices \
    && command -v uhd_config_info \
    && command -v uhd_usrp_probe \
    && command -v uhd_image_loader \
    && rm -rf /opt/uhd/.git /opt/uhd/host/build

RUN git clone --depth 1 --branch "${SRSRAN_4G_VERSION}" https://github.com/srsran/srsRAN_4G.git srsran4g \
    && cd srsran4g \
    && git fetch --depth 1 origin "${SRSRAN_4G_COMMIT}" \
    && git checkout --detach "${SRSRAN_4G_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${SRSRAN_4G_COMMIT}" \
    && perl -0pi -e 's/-std=c\+\+14/-std=c++17/g' CMakeLists.txt \
    && cmake -S . -B build -DENABLE_ZEROMQ=OFF -DENABLE_UHD=ON -DENABLE_GUI=OFF -DCMAKE_CXX_FLAGS="-std=c++17" \
    && cmake --build build -j"$(nproc)" \
    && cmake --install build \
    && ldconfig \
    && command -v srsenb \
    && (srsenb --rf.device_name=uhd --version >/dev/null 2>&1 || true) \
    && rm -rf /opt/srsran4g/.git /opt/srsran4g/build

COPY entrypoint.sh /usr/local/bin/lain5g-srsran4g-uhd-entrypoint
RUN chmod +x /usr/local/bin/lain5g-srsran4g-uhd-entrypoint

ENTRYPOINT ["lain5g-srsran4g-uhd-entrypoint"]
