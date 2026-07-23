FROM ghcr.io/herlesupreeth/docker_pyhss@sha256:90206eb3cbe862bfa71e0bfaf038fe3ddbefba1df531eb2157c9642ac732e6fb

ARG LAIN5G_VERSION=1.0.0-rc.1

# pyHSS 1.0.2 prints provisioning payloads, including Ki and OPc, to stdout.
RUN sed -i '/print("JSON Data sent: " + str(json_data))/d' /pyhss/services/apiService.py

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="Lain5G-Lab Secure pyHSS" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab" \
      org.opencontainers.image.licenses="MIT AND AGPL-3.0-only AND BSD-2-Clause"

COPY runtime/ /mnt/pyhss/
