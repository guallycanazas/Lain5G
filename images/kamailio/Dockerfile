FROM debian:bookworm-slim@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818

ARG DEBIAN_FRONTEND=noninteractive
ARG LAIN5G_VERSION=1.0.0-rc.1
ARG KAMAILIO_VERSION=5.8.8
ARG KAMAILIO_COMMIT=053181eb9c3136836cb272584b582484a9a11b48

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      bison \
      build-essential \
      ca-certificates \
      flex \
      git \
      libpcre3-dev \
      libssl-dev \
      make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${KAMAILIO_VERSION}" https://github.com/kamailio/kamailio.git kamailio \
    && cd kamailio \
    && git fetch --depth 1 origin "${KAMAILIO_COMMIT}" \
    && git checkout --detach "${KAMAILIO_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${KAMAILIO_COMMIT}" \
    && cd src \
    && make cfg PREFIX=/usr/local include_modules="sl tm textops siputils xlog" \
    && make all -j"$(nproc)" \
    && make install \
    && command -v kamailio \
    && kamailio -v \
    && rm -rf /opt/kamailio/.git

ENTRYPOINT ["kamailio"]
