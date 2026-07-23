FROM debian@sha256:60eac759739651111db372c07be67863818726f754804b8707c90979bda511df

ARG LAIN5G_VERSION=1.0.0-rc.1

ENV DEBIAN_FRONTEND=noninteractive
ENV DIST=bookworm
ENV REL=26.0

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates gnupg wget && \
    wget -q https://rtpengine.dfx.at/26.0/pool/main/r/rtpengine-dfx-repo-keyring/rtpengine-dfx-repo-keyring_1.0_all.deb && \
    echo "78fe26f0251138f4e3c749c88dc4df29666c8efe0823858d3a4ab49d2fa2e088  rtpengine-dfx-repo-keyring_1.0_all.deb" | sha256sum -c - && \
    dpkg -i rtpengine-dfx-repo-keyring_1.0_all.deb && \
    rm rtpengine-dfx-repo-keyring_1.0_all.deb && \
    printf 'deb [signed-by=/usr/share/keyrings/dfx.at-rtpengine-archive-keyring.gpg] https://rtpengine.dfx.at/%s %s main\n' "$REL" "$DIST" > /etc/apt/sources.list.d/dfx.at-rtpengine.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends iproute2 iptables nftables rtpengine && \
    rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.version="${LAIN5G_VERSION}" \
      org.opencontainers.image.title="Lain5G-Lab Real IMS RTPengine" \
      org.opencontainers.image.source="https://github.com/guallycanazas/Lain5G-Lab" \
      org.opencontainers.image.licenses="MIT AND GPL-3.0-only AND BSD-2-Clause"

COPY runtime/ /mnt/rtpengine/
RUN chmod 0755 /mnt/rtpengine/rtpengine_init.sh

CMD ["/mnt/rtpengine/rtpengine_init.sh"]
