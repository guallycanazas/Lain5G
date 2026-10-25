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
SUBSCRIBER_IMSI = os.environ.get("SUBSCRIBER_IMSI", "")
SUBSCRIBER_MSISDN = os.environ.get("SUBSCRIBER_MSISDN", "")
IMS_AUTH_PASSWORD = os.environ.get("IMS_AUTH_PASSWORD", "")
BIND_IP = os.environ.get("SCSCF_BIND_IP", "10.41.0.22")


def configured_users() -> dict[str, dict[str, str]]:
    users: dict[str, dict[str, str]] = {}
    if SUBSCRIBER_IMSI and SUBSCRIBER_MSISDN and IMS_AUTH_PASSWORD:
        users[SUBSCRIBER_MSISDN] = {
            "impi": f"{SUBSCRIBER_IMSI}@{IMS_DOMAIN}",
            "impu": f"sip:{SUBSCRIBER_MSISDN}@{IMS_DOMAIN}",
            "password": IMS_AUTH_PASSWORD,
        }
    for label, default_number, default_password in (
        ("A", "10004", "virtual-phone-a-lab-only"),
        ("B", "10001", "virtual-phone-b-lab-only"),
    ):
        number = os.environ.get(f"VIRTUAL_PHONE_{label}_NUMBER", default_number)
        users[number] = {
            "impi": f"{number}@{IMS_DOMAIN}",
            "impu": f"sip:{number}@{IMS_DOMAIN}",
            "password": os.environ.get(f"VIRTUAL_PHONE_{label}_PASSWORD", default_password),
        }
    return users


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


def sip_user(uri: str) -> str:
    match = re.search(r"sip:([^@;>]+)@", uri, re.IGNORECASE)
    return match.group(1) if match else ""


def activity_flow_id(headers: dict[str, list[str]]) -> str:
    call_id = first(headers, "call-id")
    cseq = first(headers, "cseq").split(" ", 1)[0]
    return hashlib.sha256(f"{call_id}:{cseq}".encode("utf-8")).hexdigest()[:12]


def log_activity(
    *,
    method: str,
    from_user: str,
    to_user: str,
    flow_id: str,
    phase: str,
    status: int | str,
) -> None:
    # Deliberately record signaling metadata only: never include SIP message bodies.
    print(
        f"IMS_ACTIVITY method={method} from={from_user or 'unknown'} to={to_user or 'unknown'} "
        f"flow={flow_id} phase={phase} status={status}",
        flush=True,
    )


def contact_address(value: str) -> tuple[str, int] | None:
    match = re.search(r"@([^@>:;]+):(\d+)", value, re.IGNORECASE)
    if not match:
        return None
    try:
        return match.group(1), int(match.group(2))
    except ValueError:
        return None


def branch_from_via(value: str) -> str:
    match = re.search(r";branch=([^;\s]+)", value, re.IGNORECASE)
    return match.group(1) if match else ""


def add_via(message: str, branch: str) -> bytes:
    first, separator, rest = message.partition("\r\n")
    via = f"Via: SIP/2.0/UDP {BIND_IP}:5060;branch={branch};rport"
    return f"{first}\r\n{via}\r\n{rest}".encode("utf-8")


def remove_top_via(message: str) -> str:
    return re.sub(r"(?im)^Via:[^\r\n]*\r\n", "", message, count=1)


def forward_request(message: str, branch: str) -> bytes:
    return add_via(message, branch)


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, 5060))
    users = configured_users()
    by_impi = {user["impi"]: (number, user) for number, user in users.items()}
    nonces = {number: secrets.token_hex(16) for number in users}
    contacts: dict[str, tuple[str, int]] = {}
    transactions: dict[str, tuple[tuple[str, int], str, str, str, str]] = {}
    print(f"SCSCF_READY users={len(users)}", flush=True)
    while True:
        data, address = sock.recvfrom(65535)
        message = data.decode("utf-8", errors="replace")
        if message.startswith("SIP/2.0 "):
            headers = parse_headers(message)
            branch = branch_from_via(first(headers, "via"))
            try:
                status_code = int(message.split()[1])
            except (IndexError, ValueError):
                status_code = 0
            transaction = transactions.get(branch)
            if transaction is not None:
                upstream, method, from_user, to_user, flow_id = transaction
                if method in {"INVITE", "MESSAGE", "BYE", "CANCEL"}:
                    log_activity(method=method, from_user=from_user, to_user=to_user, flow_id=flow_id, phase="response", status=status_code)
                sock.sendto(remove_top_via(message).encode("utf-8"), upstream)
                if status_code >= 200:
                    transactions.pop(branch, None)
            else:
                print("SCSCF_UNMATCHED_RESPONSE", flush=True)
            continue

        headers = parse_headers(message)
        method = message.split(" ", 1)[0].upper()
        if method == "REGISTER":
            authorization = parse_digest(first(headers, "authorization"))
            username = authorization.get("username", "")
            account = by_impi.get(username)
            if account is None:
                number = sip_user(first(headers, "to"))
                user = users.get(number)
                account = (number, user) if user else None
            if account is None:
                sock.sendto(response(message, 403, "Unknown Subscriber"), address)
                continue
            number, user = account
            if not first(headers, "authorization"):
                print(f"SCSCF_INITIAL_REGISTER impi={user['impi']} impu={user['impu']}", flush=True)
                challenge = (
                    f'WWW-Authenticate: Digest realm="{IMS_DOMAIN}", nonce="{nonces[number]}", '
                    'algorithm=MD5, qop="auth"'
                )
                sock.sendto(response(message, 401, "Unauthorized", [challenge]), address)
                print(f"SCSCF_SENT_401_UNAUTHORIZED user={number}", flush=True)
                continue
            digest = authorization
            uri = digest.get("uri", "")
            qop = digest.get("qop", "")
            ha1 = md5(f"{user['impi']}:{IMS_DOMAIN}:{user['password']}")
            ha2 = md5(f"REGISTER:{uri}")
            if qop:
                expected = md5(f"{ha1}:{nonces[number]}:{digest.get('nc', '')}:{digest.get('cnonce', '')}:{qop}:{ha2}")
            else:
                expected = md5(f"{ha1}:{nonces[number]}:{ha2}")
            valid = (
                digest.get("realm") == IMS_DOMAIN
                and digest.get("nonce") == nonces[number]
                and sip_user(first(headers, "to")) == number
                and secrets.compare_digest(digest.get("response", ""), expected)
            )
            target = contact_address(first(headers, "contact"))
            if not valid or target is None:
                sock.sendto(response(message, 403, "Authentication Failed"), address)
                print(f"SCSCF_AUTH_FAILED user={number} sent=403", flush=True)
                continue
            contacts[number] = target
            print(f"SCSCF_AUTH_REGISTER impi={user['impi']} impu={user['impu']}", flush=True)
            sock.sendto(response(message, 200, "OK", ["Expires: 3600"]), address)
            print("SCSCF_SENT_200_OK", flush=True)
            print(f"SCSCF_REGISTERED user={number} contact={target[0]}:{target[1]}", flush=True)
            continue

        target_number = sip_user(first(headers, "to"))
        source_number = sip_user(first(headers, "from"))
        flow_id = activity_flow_id(headers)
        target = contacts.get(target_number)
        if target is None:
            sock.sendto(response(message, 480, "Temporarily Unavailable"), address)
            print(f"SCSCF_TARGET_NOT_REGISTERED user={target_number or 'unknown'} method={method}", flush=True)
            if method in {"INVITE", "MESSAGE", "BYE", "CANCEL"}:
                log_activity(method=method, from_user=source_number, to_user=target_number, flow_id=flow_id, phase="not_routed", status=480)
            continue
        if method == "ACK":
            sock.sendto(data, target)
            print(f"SCSCF_ROUTED_ACK target={target_number}", flush=True)
            continue
        if method not in {"INVITE", "BYE", "CANCEL", "MESSAGE"}:
            sock.sendto(response(message, 405, "Method Not Allowed"), address)
            continue

        if method == "INVITE":
            sock.sendto(response(message, 100, "Trying"), address)
        log_activity(method=method, from_user=source_number, to_user=target_number, flow_id=flow_id, phase="forwarded", status="pending")
        branch = "z9hG4bK" + secrets.token_hex(8)
        transactions[branch] = (address, method, source_number, target_number, flow_id)
        sock.sendto(forward_request(message, branch), target)
        print(f"SCSCF_FORWARDED method={method} target={target_number}", flush=True)


if __name__ == "__main__":
    main()
