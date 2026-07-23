ARG BASE_IMAGE=ghcr.io/herlesupreeth/docker_open5gs@sha256:441d40e16f76ae79fc25eaaa92245850ed833bdd3d0d0dc78acbffd958cdc2c6
FROM ${BASE_IMAGE}

ARG LAIN5G_VERSION=1.0.0-rc.1

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="Lain5G-Lab Real IMS Open5GS" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab" \
      org.opencontainers.image.licenses="MIT AND AGPL-3.0-only AND BSD-2-Clause" \
      org.opencontainers.image.description="Pinned Open5GS binaries with Lain5G-Lab-packaged role configurations"

# The upstream image installs demo HN keys. Hide them from the final filesystem;
# UDM creates fresh keys in its runtime-only key directory before startup.
RUN rm -f /open5gs/install/etc/open5gs/hnet/*.key

COPY roles/ /mnt/
