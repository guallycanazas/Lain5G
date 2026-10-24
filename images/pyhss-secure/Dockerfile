FROM ubuntu:22.04@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982

ARG DEBIAN_FRONTEND=noninteractive
ARG LAIN5G_VERSION=1.1.6
ARG PYHSS_COMMIT=71a91f6d9e6b910a74750e266edb7642ca8f9971

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates git python3 python3-pip python3-dev python3-setuptools \
      python3-wheel build-essential default-libmysqlclient-dev libpq-dev \
      default-mysql-client python3-mysqldb libsctp-dev libtalloc-dev redis-server patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /pyhss
COPY patches/redis6-compat.patch /tmp/redis6-compat.patch
RUN git clone --depth 1 --branch 1.0.2 https://github.com/nickvsnetworking/pyhss.git /tmp/pyhss \
    && cd /tmp/pyhss \
    && git fetch --depth 1 origin "${PYHSS_COMMIT}" \
    && git checkout --detach "${PYHSS_COMMIT}" \
    && test "$(git rev-parse HEAD)" = "${PYHSS_COMMIT}" \
    && sed -i '/^mysqlclient$/d' requirements.txt \
    && pip3 install --no-cache-dir -r requirements.txt \
    && cp -a . /pyhss/ \
    && rm -rf /pyhss/.git /tmp/pyhss \
    && patch -p1 -d /pyhss < /tmp/redis6-compat.patch \
    && sed -i '/print("JSON Data sent: " + str(json_data))/d' /pyhss/services/apiService.py \
    && mkdir -p /pyhss/log

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="OpenLain5G Secure pyHSS" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G" \
      org.opencontainers.image.licenses="MIT AND AGPL-3.0-only AND BSD-2-Clause" \
      org.opencontainers.image.description="OpenLain5G-built pyHSS from the pinned 1.0.2 source release"

COPY runtime/ /mnt/pyhss/
RUN chmod 0755 /mnt/pyhss/pyhss_init.sh

ENTRYPOINT ["/mnt/pyhss/pyhss_init.sh"]
CMD ["python3", "hssService.py"]
