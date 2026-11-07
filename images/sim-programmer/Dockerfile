FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS pysim-build

ARG PYSIM_COMMIT=c4266f33df8dcd850469fc06330d4abdb304516c

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git libpcsclite-dev swig \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip==25.1.1 \
    && python -m pip install --no-cache-dir \
        'pyscard>=2.0,<3' pyserial pytlv 'cmd2>=2.6.2,<4' jsonpath-ng \
        'construct>=2.10.70' bidict 'pyosmocom>=0.0.12' 'pyyaml>=5.4' \
        termcolor colorlog pycryptodomex packaging asn1tools \
    && git clone --filter=blob:none https://gitea.osmocom.org/sim-card/pysim.git /opt/pysim \
    && git -C /opt/pysim checkout --detach "${PYSIM_COMMIT}" \
    && rm -rf /opt/pysim/.git

FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

ARG LAIN5G_VERSION=1.1.9

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G" \
      org.opencontainers.image.title="OpenLain5G SIM programmer bridge"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/pysim \
    PCSCLITE_CSOCK_NAME=/run/pcscd/pcscd.comm

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpcsclite1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=pysim-build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=pysim-build /opt/pysim /opt/pysim

WORKDIR /app
COPY server.py /app/server.py

USER 0:0
EXPOSE 8123
CMD ["python", "/app/server.py"]
