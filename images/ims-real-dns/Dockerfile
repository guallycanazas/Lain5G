FROM ubuntu@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982

ARG LAIN5G_VERSION=1.0.0-rc.1

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends bind9 iproute2 iputils-ping net-tools tcpdump && \
    rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="Lain5G-Lab Real IMS DNS" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab" \
      org.opencontainers.image.licenses="MIT AND BSD-2-Clause"

COPY runtime/ /mnt/dns/
RUN chmod 0755 /mnt/dns/dns_init.sh

CMD ["/mnt/dns/dns_init.sh"]
