FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

ARG LAIN5G_VERSION=1.0.0-rc.1

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab"

WORKDIR /opt/lain5g-ims
COPY scscf_server.py sip_register_client.py ./

ENTRYPOINT ["python3"]
