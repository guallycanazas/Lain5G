ARG BASE_IMAGE=ghcr.io/herlesupreeth/docker_kamailio@sha256:67dc92b423ca5ef0b827a049d0cabeff741f3eafd9222608036494f4d7611821
FROM ${BASE_IMAGE}

ARG LAIN5G_VERSION=1.0.0-rc.1

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="Lain5G-Lab Real IMS Kamailio" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab" \
      org.opencontainers.image.licenses="MIT AND GPL-2.0-only AND BSD-2-Clause" \
      org.opencontainers.image.description="Pinned Kamailio binaries with Lain5G-Lab-packaged P/I/S-CSCF configurations"

COPY roles/ /mnt/
