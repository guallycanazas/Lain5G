ARG BASE_IMAGE=ghcr.io/herlesupreeth/docker_mysql@sha256:324d3d4c5089feea787684f0dbf1a646dde8d356170085ac0b6538aee6910057
FROM ${BASE_IMAGE}

ARG LAIN5G_VERSION=1.1.1

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="OpenLain5G Real IMS MySQL" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G" \
      org.opencontainers.image.licenses="MIT AND GPL-2.0-only AND BSD-2-Clause"

COPY runtime/mysql_init.sh /mysql_init.sh
RUN chmod 0755 /mysql_init.sh
