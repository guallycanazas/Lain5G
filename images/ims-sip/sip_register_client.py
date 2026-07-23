#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
import secrets
import socket
import sys
import time


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"SIP_CLIENT_CONFIG_ERROR missing {name}", flush=True)
        sys.exit(2)
    return value


def env_default(name: str, default: str) -> str:
    return os.environ.get(name, default) or default


IMS_DOMAIN = env("IMS_DOMAIN")
PCSCF_DOMAIN = env_default("PCSCF_DOMAIN", f"pcscf.{IMS_DOMAIN}")
ICSCF_DOMAIN = env_default("ICSCF_DOMAIN", f"icscf.{IMS_DOMAIN}")
SCSCF_DOMAIN = env_default("SCSCF_DOMAIN", f"scscf.{IMS_DOMAIN}")
SUBSCRIBER_IMSI = env("SUBSCRIBER_IMSI")
SUBSCRIBER_MSISDN = env("SUBSCRIBER_MSISDN")
IMS_AUTH_PASSWORD = env("IMS_AUTH_PASSWORD")
IMPI = f"{SUBSCRIBER_IMSI}@{IMS_DOMAIN}"
IMPU = f"sip:{SUBSCRIBER_MSISDN}@{IMS_DOMAIN}"
REGISTER_URI = f"sip:{IMS_DOMAIN}"
CALL_ID = os.environ.get("SIP_CALL_ID", secrets.token_hex(8) + "@lain5g")
EXPECTED_IMS_IP = env_default("SIP_EXPECTED_IMS_IP", "10.41.0.20")
EXPECTED_PCSCF_IP = env_default("SIP_EXPECTED_PCSCF_IP", EXPECTED_IMS_IP)
EXPECTED_ICSCF_IP = env_default("SIP_EXPECTED_ICSCF_IP", "10.41.0.21")
EXPECTED_SCSCF_IP = env_default("SIP_EXPECTED_SCSCF_IP", "10.41.0.22")
SIP_DNS_SERVER = os.environ.get("SIP_DNS_SERVER", "")


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def resolve(name: str, expected: str | None = None) -> str:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            address = socket.gethostbyname(name)
            if expected and address != expected:
                raise RuntimeError(f"unexpected address {address}, expected {expected}")
            print(f"SIP_CLIENT_DNS_RESOLVED {name}={address}", flush=True)
            return address
        except Exception as exc:  # pragma: no cover - exercised in container
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"DNS resolution failed for {name}: {last_error}")


def resolve_via_dns_server(name: str, expected: str | None = None) -> str:
    if not SIP_DNS_SERVER:
        return resolve(name, expected)
    query_id = secrets.token_bytes(2)
    labels = b"".join(bytes([len(part)]) + part.encode("ascii") for part in name.rstrip(".").split(".")) + b"\x00"
    query = query_id + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" + labels + b"\x00\x01\x00\x01"
    last_error: Exception | None = None
    for _ in range(30):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(query, (SIP_DNS_SERVER, 53))
            data, _ = sock.recvfrom(512)
            if data[:2] != query_id:
                raise RuntimeError("DNS response id mismatch")
            answer_count = int.from_bytes(data[6:8], "big")
            offset = 12
            while data[offset] != 0:
                offset += data[offset] + 1
            offset += 5
            for _answer in range(answer_count):
                if data[offset] & 0xC0 == 0xC0:
                    offset += 2
                else:
                    while data[offset] != 0:
                        offset += data[offset] + 1
                    offset += 1
                rtype = int.from_bytes(data[offset:offset + 2], "big")
                rclass = int.from_bytes(data[offset + 2:offset + 4], "big")
                rdlength = int.from_bytes(data[offset + 8:offset + 10], "big")
                rdata = data[offset + 10:offset + 10 + rdlength]
                offset += 10 + rdlength
                if rtype == 1 and rclass == 1 and rdlength == 4:
                    address = socket.inet_ntoa(rdata)
                    if expected and address != expected:
                        raise RuntimeError(f"unexpected address {address}, expected {expected}")
                    print(f"SIP_CLIENT_DNS_RESOLVED {name}={address} server={SIP_DNS_SERVER}", flush=True)
                    return address
            raise RuntimeError("DNS A answer not found")
        except Exception as exc:  # pragma: no cover - exercised in container
            last_error = exc
            time.sleep(1)
        finally:
            try:
                sock.close()
            except Exception:
                pass
    raise RuntimeError(f"DNS resolution failed for {name} via {SIP_DNS_SERVER}: {last_error}")


def parse_code(message: str) -> int:
    match = re.match(r"SIP/2\.0\s+(\d{3})", message)
    return int(match.group(1)) if match else 0


def header(message: str, name: str) -> str:
    prefix = name.lower() + ":"
    for line in message.split("\r\n"):
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def parse_digest(header_value: str) -> dict[str, str]:
    if header_value.lower().startswith("digest "):
        header_value = header_value[7:]
    values: dict[str, str] = {}
    for key, quoted, bare in re.findall(r'(\w+)=(?:"([^"]*)"|([^,\s]+))', header_value):
        values[key.lower()] = quoted or bare
    return values


def build_register(cseq: int, local_ip: str, branch: str, authorization: str | None = None) -> bytes:
    lines = [
        f"REGISTER {REGISTER_URI} SIP/2.0",
        f"Via: SIP/2.0/UDP {local_ip}:5062;branch=z9hG4bK{branch};rport",
        "Max-Forwards: 70",
        f"From: <{IMPU}>;tag=lain5g",
        f"To: <{IMPU}>",
        f"Call-ID: {CALL_ID}",
        f"CSeq: {cseq} REGISTER",
        f"Contact: <sip:{IMPI}@{local_ip}:5062>",
        "Expires: 3600",
        "User-Agent: Lain5G-Lab-SIP-Probe",
    ]
    if authorization:
        lines.append(f"Authorization: {authorization}")
    lines.append("Content-Length: 0")
    lines.extend(["", ""])
    return "\r\n".join(lines).encode("utf-8")


def digest_authorization(challenge: str) -> str:
    digest = parse_digest(challenge)
    realm = digest["realm"]
    nonce = digest["nonce"]
    qop = "auth"
    nc = "00000001"
    cnonce = secrets.token_hex(8)
    ha1 = md5(f"{IMPI}:{realm}:{IMS_AUTH_PASSWORD}")
    ha2 = md5(f"REGISTER:{REGISTER_URI}")
    response = md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}")
    return (
        f'Digest username="{IMPI}", realm="{realm}", nonce="{nonce}", uri="{REGISTER_URI}", '
        f'response="{response}", algorithm=MD5, qop={qop}, nc={nc}, cnonce="{cnonce}"'
    )


def receive(sock: socket.socket) -> str:
    data, _ = sock.recvfrom(65535)
    return data.decode("utf-8", errors="replace")


def main() -> int:
    resolve_via_dns_server(IMS_DOMAIN, EXPECTED_IMS_IP)
    pcscf_ip = resolve_via_dns_server(PCSCF_DOMAIN, EXPECTED_PCSCF_IP)
    resolve_via_dns_server(ICSCF_DOMAIN, EXPECTED_ICSCF_IP)
    resolve_via_dns_server(SCSCF_DOMAIN, EXPECTED_SCSCF_IP)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    sock.bind(("0.0.0.0", 5062))
    sock.connect((pcscf_ip, 5060))
    local_ip = sock.getsockname()[0]

    sock.send(build_register(1, local_ip, secrets.token_hex(8)))
    print(f"SIP_CLIENT_INITIAL_REGISTER_SENT impi={IMPI} impu={IMPU}", flush=True)
    first_response = receive(sock)
    first_code = parse_code(first_response)
    print(f"SIP_CLIENT_CHALLENGE_RECEIVED code={first_code}", flush=True)
    if first_code != 401:
        print(f"SIP_REGISTER_RESULT=FAIL final_code={first_code}", flush=True)
        return 1
    challenge = header(first_response, "WWW-Authenticate")
    if not challenge:
        print("SIP_REGISTER_RESULT=FAIL reason=missing_challenge", flush=True)
        return 1

    authorization = digest_authorization(challenge)
    sock.send(build_register(2, local_ip, secrets.token_hex(8), authorization))
    print(f"SIP_CLIENT_AUTH_REGISTER_SENT impi={IMPI} impu={IMPU}", flush=True)
    final_response = receive(sock)
    final_code = parse_code(final_response)
    print(f"SIP_CLIENT_FINAL_RESPONSE code={final_code}", flush=True)
    if final_code == 200:
        print("SIP_REGISTER_RESULT=PASS final_code=200", flush=True)
        return 0
    print(f"SIP_REGISTER_RESULT=FAIL final_code={final_code}", flush=True)
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SIP_REGISTER_RESULT=FAIL error={exc}", flush=True)
        raise SystemExit(1)
