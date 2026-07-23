#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
import secrets
import socket
import sys


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"SCSCF_CONFIG_ERROR missing {name}", flush=True)
        sys.exit(2)
    return value


IMS_DOMAIN = env("IMS_DOMAIN")
SUBSCRIBER_IMSI = env("SUBSCRIBER_IMSI")
SUBSCRIBER_MSISDN = env("SUBSCRIBER_MSISDN")
IMS_AUTH_PASSWORD = env("IMS_AUTH_PASSWORD")
IMPI = f"{SUBSCRIBER_IMSI}@{IMS_DOMAIN}"
IMPU = f"sip:{SUBSCRIBER_MSISDN}@{IMS_DOMAIN}"
NONCE = secrets.token_hex(16)
BIND_IP = os.environ.get("SCSCF_BIND_IP", "10.41.0.22")


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def parse_headers(message: str) -> dict[str, list[str]]:
    headers: dict[str, list[str]] = {}
    for line in message.split("\r\n")[1:]:
        if not line:
            break
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers.setdefault(name.strip().lower(), []).append(value.strip())
    return headers


def first(headers: dict[str, list[str]], name: str) -> str:
    values = headers.get(name.lower(), [])
    return values[0] if values else ""


def parse_digest(header: str) -> dict[str, str]:
    if header.lower().startswith("digest "):
        header = header[7:]
    values: dict[str, str] = {}
    for key, quoted, bare in re.findall(r'(\w+)=(?:"([^"]*)"|([^,\s]+))', header):
        values[key.lower()] = quoted or bare
    return values


def valid_authorization(message: str, headers: dict[str, list[str]]) -> bool:
    authorization = first(headers, "authorization")
    if not authorization:
        return False
    digest = parse_digest(authorization)
    username = digest.get("username", "")
    realm = digest.get("realm", "")
    nonce = digest.get("nonce", "")
    uri = digest.get("uri", "")
    response = digest.get("response", "")
    qop = digest.get("qop", "")
    nc = digest.get("nc", "")
    cnonce = digest.get("cnonce", "")
    if username != IMPI or realm != IMS_DOMAIN or nonce != NONCE or not uri or not response:
        return False
    method = message.split(" ", 1)[0]
    ha1 = md5(f"{IMPI}:{IMS_DOMAIN}:{IMS_AUTH_PASSWORD}")
    ha2 = md5(f"{method}:{uri}")
    if qop:
        expected = md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}")
    else:
        expected = md5(f"{ha1}:{nonce}:{ha2}")
    return secrets.compare_digest(response, expected)


def response(message: str, status: int, reason: str, extra_headers: list[str] | None = None) -> bytes:
    headers = parse_headers(message)
    lines = [f"SIP/2.0 {status} {reason}"]
    lines.extend(f"Via: {via}" for via in headers.get("via", []))
    for name in ("from", "to", "call-id", "cseq"):
        value = first(headers, name)
        if value:
            lines.append(f"{name.title()}: {value}")
    if extra_headers:
        lines.extend(extra_headers)
    lines.append("Content-Length: 0")
    lines.extend(["", ""])
    return "\r\n".join(lines).encode("utf-8")


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, 5060))
    print(f"SCSCF_READY impi={IMPI} impu={IMPU}", flush=True)
    while True:
        data, address = sock.recvfrom(65535)
        message = data.decode("utf-8", errors="replace")
        if not message.startswith("REGISTER "):
            sock.sendto(response(message, 405, "Method Not Allowed"), address)
            continue
        headers = parse_headers(message)
        if not first(headers, "authorization"):
            print(f"SCSCF_INITIAL_REGISTER impi={IMPI} impu={IMPU}", flush=True)
            challenge = (
                f'WWW-Authenticate: Digest realm="{IMS_DOMAIN}", nonce="{NONCE}", '
                'algorithm=MD5, qop="auth"'
            )
            sock.sendto(response(message, 401, "Unauthorized", [challenge]), address)
            print("SCSCF_SENT_401_UNAUTHORIZED", flush=True)
            continue
        print(f"SCSCF_AUTH_REGISTER impi={IMPI} impu={IMPU}", flush=True)
        if valid_authorization(message, headers):
            sock.sendto(response(message, 200, "OK", ["Expires: 3600"]), address)
            print("SCSCF_SENT_200_OK", flush=True)
        else:
            challenge = (
                f'WWW-Authenticate: Digest realm="{IMS_DOMAIN}", nonce="{NONCE}", '
                'algorithm=MD5, qop="auth"'
            )
            sock.sendto(response(message, 403, "Forbidden", [challenge]), address)
            print("SCSCF_AUTH_FAILED sent=403", flush=True)


if __name__ == "__main__":
    main()
