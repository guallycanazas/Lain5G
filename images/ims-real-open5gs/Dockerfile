ARG BASE_IMAGE=gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c
FROM ${BASE_IMAGE}

ARG LAIN5G_VERSION=1.1.7

# The role configs refer to Open5GS' bundled freeDiameter extensions through
# LD_LIBRARY_PATH/freeDiameter. The base image installs these under this path.
ENV LD_LIBRARY_PATH=/usr/local/lib/x86_64-linux-gnu

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="OpenLain5G Real IMS Open5GS" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G" \
      org.opencontainers.image.licenses="MIT AND AGPL-3.0-only AND BSD-2-Clause" \
      org.opencontainers.image.description="Open5GS built from upstream source with OpenLain5G's IMS/EPC role configuration"

COPY runtime/open5gs-ims-entrypoint.sh /usr/local/bin/open5gs-ims-entrypoint
COPY roles/ /mnt/

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-click \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /usr/local/etc/open5gs/hnet/*.key \
    && mkdir -p /open5gs \
    && ln -sfn /usr/local /open5gs/install \
    && chmod 0755 /usr/local/bin/open5gs-ims-entrypoint

ENTRYPOINT ["/usr/local/bin/open5gs-ims-entrypoint"]
