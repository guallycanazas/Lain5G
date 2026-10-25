#!/usr/bin/env python3
"""Run two software-only SIP phones through the isolated 4G IMS simulator."""
from __future__ import annotations

import hashlib
import os
import queue
import re
import secrets
import socket
import struct
import threading
import time
from dataclasses import dataclass


IMS_DOMAIN = os.environ["IMS_DOMAIN"]
PHONE_IP = os.environ.get("SIP_PHONE_BIND_IP", "10.41.0.33")
PCSCF_DOMAIN = os.environ.get("SIP_PCSCF_DOMAIN", f"pcscf.{IMS_DOMAIN}")
PHONE_A_NUMBER = os.environ.get("VIRTUAL_PHONE_A_NUMBER", "10004")
PHONE_A_PASSWORD = os.environ.get("VIRTUAL_PHONE_A_PASSWORD", "virtual-phone-a-lab-only")
PHONE_B_NUMBER = os.environ.get("VIRTUAL_PHONE_B_NUMBER", "10001")
PHONE_B_PASSWORD = os.environ.get("VIRTUAL_PHONE_B_PASSWORD", "virtual-phone-b-lab-only")
MEDIA_FRAMES = 5
MEDIA_PAYLOAD = b"\xff" * 160  # PCMU silence at 20 ms per frame.


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def parse_headers(message: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in message.split("\r\n")[1:]:
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            result.setdefault(key.strip().lower(), []).append(value.strip())
    return result


def first(headers: dict[str, list[str]], name: str) -> str:
    values = headers.get(name.lower(), [])
    return values[0] if values else ""


def parse_digest(value: str) -> dict[str, str]:
    if value.lower().startswith("digest "):
        value = value[7:]
    return {key.lower(): quoted or bare for key, quoted, bare in re.findall(r'(\w+)=(?:"([^"]*)"|([^,\s]+))', value)}


def sip_uri(number: str) -> str:
    return f"sip:{number}@{IMS_DOMAIN}"


def sip_response_code(message: str) -> int:
    match = re.match(r"SIP/2\.0\s+(\d{3})", message)
    return int(match.group(1)) if match else 0


def body_of(message: str) -> str:
    return message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else ""


def make_sdp(ip: str, port: int, origin: str) -> str:
    return (
        f"v=0\r\n"
        f"o={origin} 1 1 IN IP4 {ip}\r\n"
        f"s=OpenLain5G virtual call\r\n"
        f"c=IN IP4 {ip}\r\n"
        f"t=0 0\r\n"
        f"m=audio {port} RTP/AVP 0\r\n"
        f"a=rtpmap:0 PCMU/8000\r\n"
        f"a=sendrecv\r\n"
    )


def media_address(sdp: str) -> tuple[str, int]:
    connection = re.search(r"(?m)^c=IN IP4 ([^\r\n]+)", sdp)
    port = re.search(r"(?m)^m=audio (\d+)", sdp)
    if not connection or not port:
        raise RuntimeError("SIP response did not contain a usable audio SDP")
    return connection.group(1), int(port.group(1))


def top_via_address(message: str) -> tuple[str, int]:
    via = first(parse_headers(message), "via")
    match = re.search(r"SIP/2\.0/UDP\s+([^:;\s]+):(\d+)", via, re.IGNORECASE)
    if not match:
        raise RuntimeError("SIP request did not include a routable top Via")
    return match.group(1), int(match.group(2))


@dataclass
class PhoneConfig:
    number: str
    password: str
    port: int
    media_port: int


class VirtualPhone:
    def __init__(self, config: PhoneConfig, proxy: tuple[str, int]) -> None:
        self.config = config
        self.impi = f"{config.number}@{IMS_DOMAIN}"
        self.impu = sip_uri(config.number)
        self.proxy = proxy
        self.call_id = f"{secrets.token_hex(8)}@virtual-phone"
        self.from_tag = secrets.token_hex(6)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((PHONE_IP, config.port))
        self.socket.settimeout(0.2)
        self.rtp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp.bind((PHONE_IP, config.media_port))
        self.rtp.settimeout(0.2)
        self.responses: queue.Queue[str] = queue.Queue()
        self.rtp_packets: queue.Queue[bytes] = queue.Queue()
        self.provisional_codes: dict[str, set[int]] = {}
        self.invite_received = threading.Event()
        self.ack_received = threading.Event()
        self.bye_received = threading.Event()
        self.sms_received = threading.Event()
        self.remote_tag = ""
        self.remote_media: tuple[str, int] | None = None
        self.sms_body = ""
        self._stopping = threading.Event()
        self._reader = threading.Thread(target=self._read_signaling, daemon=True)
        self._rtp_reader = threading.Thread(target=self._read_rtp, daemon=True)

    @property
    def contact(self) -> str:
        return f"<sip:{self.config.number}@{PHONE_IP}:{self.config.port}>"

    def start(self) -> None:
        self._reader.start()
        self._rtp_reader.start()

    def close(self) -> None:
        self._stopping.set()
        self.socket.close()
        self.rtp.close()

    def _read_signaling(self) -> None:
        while not self._stopping.is_set():
            try:
                data, _ = self.socket.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                return
            message = data.decode("utf-8", errors="replace")
            if message.startswith("SIP/2.0 "):
                self.responses.put(message)
                continue
            self._handle_request(message)

    def _read_rtp(self) -> None:
        while not self._stopping.is_set():
            try:
                data, _ = self.rtp.recvfrom(2048)
                self.rtp_packets.put(data)
            except socket.timeout:
                continue
            except OSError:
                return

    def _response(self, request: str, code: int, reason: str, *, sdp: str = "", tag: str = "") -> None:
        headers = parse_headers(request)
        lines = [f"SIP/2.0 {code} {reason}"]
        lines.extend(f"Via: {value}" for value in headers.get("via", []))
        lines.append(f"From: {first(headers, 'from')}")
        to_value = first(headers, "to")
        if tag and not re.search(r";tag=", to_value, re.IGNORECASE):
            to_value += f";tag={tag}"
        lines.append(f"To: {to_value}")
        lines.append(f"Call-ID: {first(headers, 'call-id')}")
        lines.append(f"CSeq: {first(headers, 'cseq')}")
        if code in {180, 200} and first(headers, "cseq").endswith(" INVITE"):
            lines.append(f"Contact: {self.contact}")
        if sdp:
            lines.append("Content-Type: application/sdp")
        payload = sdp.encode("utf-8")
        lines.append(f"Content-Length: {len(payload)}")
        packet = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + payload
        self.socket.sendto(packet, top_via_address(request))

    def _handle_request(self, message: str) -> None:
        method = message.split(" ", 1)[0].upper()
        if method == "INVITE":
            headers = parse_headers(message)
            self.remote_media = media_address(body_of(message))
            self.remote_tag = secrets.token_hex(6)
            self._response(message, 180, "Ringing", tag=self.remote_tag)
            self._response(
                message,
                200,
                "OK",
                sdp=make_sdp(PHONE_IP, self.config.media_port, self.config.number),
                tag=self.remote_tag,
            )
            self.invite_received.set()
            print(f"VIRTUAL_PHONE_RINGING user={self.config.number}", flush=True)
        elif method == "ACK":
            self.ack_received.set()
            print(f"VIRTUAL_PHONE_ACK user={self.config.number}", flush=True)
        elif method == "BYE":
            self._response(message, 200, "OK")
            self.bye_received.set()
            print(f"VIRTUAL_PHONE_CALL_ENDED user={self.config.number}", flush=True)
        elif method == "MESSAGE":
            self.sms_body = body_of(message)
            self._response(message, 200, "OK")
            self.sms_received.set()
            print(f"VIRTUAL_PHONE_MESSAGE_RECEIVED user={self.config.number}", flush=True)
        elif method == "CANCEL":
            self._response(message, 200, "OK")
        else:
            self._response(message, 405, "Method Not Allowed")

    def _wait_response(self, cseq: str, expected: set[int], timeout: float = 8.0) -> str:
        deadline = time.monotonic() + timeout
        deferred: list[str] = []
        try:
            while time.monotonic() < deadline:
                try:
                    message = self.responses.get(timeout=max(0.05, deadline - time.monotonic()))
                except queue.Empty:
                    break
                headers = parse_headers(message)
                if first(headers, "cseq") == cseq:
                    code = sip_response_code(message)
                    if code in expected:
                        return message
                    if 100 <= code < 200:
                        self.provisional_codes.setdefault(cseq, set()).add(code)
                        continue
                    raise RuntimeError(f"SIP {cseq} received unexpected response {code}")
                deferred.append(message)
        finally:
            for item in deferred:
                self.responses.put(item)
        raise TimeoutError(f"timed out waiting for SIP {cseq} response")

    def _request(self, method: str, target: str, cseq: int, *, body: str = "", content_type: str = "") -> bytes:
        branch = secrets.token_hex(8)
        to_uri = self.impu if method == "REGISTER" else target
        lines = [
            f"{method} {target} SIP/2.0",
            f"Via: SIP/2.0/UDP {PHONE_IP}:{self.config.port};branch=z9hG4bK{branch};rport",
            "Max-Forwards: 70",
            f"From: <{self.impu}>;tag={self.from_tag}",
            f"To: <{to_uri}>",
            f"Call-ID: {self.call_id}",
            f"CSeq: {cseq} {method}",
            f"Contact: {self.contact}",
            "User-Agent: OpenLain5G-VirtualPhone/1.0",
        ]
        if content_type:
            lines.append(f"Content-Type: {content_type}")
        payload = body.encode("utf-8")
        lines.append(f"Content-Length: {len(payload)}")
        return ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + payload

    def _send(self, packet: bytes) -> None:
        self.socket.sendto(packet, self.proxy)

    def register(self) -> None:
        uri = f"sip:{IMS_DOMAIN}"
        self.call_id = f"{secrets.token_hex(8)}@virtual-phone"
        initial = self._request("REGISTER", uri, 1)
        challenge = None
        for _ in range(20):
            self._send(initial)
            try:
                challenge = self._wait_response("1 REGISTER", {401}, timeout=1.0)
                break
            except TimeoutError:
                continue
        if challenge is None:
            raise TimeoutError("IMS registrar did not challenge the virtual phone")
        www_authenticate = first(parse_headers(challenge), "www-authenticate")
        params = parse_digest(www_authenticate)
        nonce = params.get("nonce", "")
        realm = params.get("realm", "")
        if not nonce or realm != IMS_DOMAIN:
            raise RuntimeError("IMS registrar returned an invalid Digest challenge")
        nc = "00000001"
        cnonce = secrets.token_hex(8)
        ha1 = md5(f"{self.impi}:{realm}:{self.config.password}")
        ha2 = md5(f"REGISTER:{uri}")
        qop = "auth"
        response_value = md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}")
        auth = (
            f'Digest username="{self.impi}", realm="{realm}", nonce="{nonce}", uri="{uri}", '
            f'response="{response_value}", algorithm=MD5, qop={qop}, nc={nc}, cnonce="{cnonce}"'
        )
        authenticated = self._request("REGISTER", uri, 2)
        text = authenticated.decode("utf-8").replace(
            "User-Agent: OpenLain5G-VirtualPhone/1.0\r\n",
            f"User-Agent: OpenLain5G-VirtualPhone/1.0\r\nAuthorization: {auth}\r\n",
            1,
        )
        self._send(text.encode("utf-8"))
        final = self._wait_response("2 REGISTER", {200})
        if sip_response_code(final) != 200:
            raise RuntimeError("virtual phone did not register")
        print(f"VIRTUAL_PHONE_REGISTER_PASS user={self.config.number} challenge=401 final=200", flush=True)

    def in_dialog_request(
        self,
        method: str,
        target: str,
        call_id: str,
        cseq: int,
        from_header: str,
        to_header: str,
    ) -> bytes:
        branch = secrets.token_hex(8)
        lines = [
            f"{method} {target} SIP/2.0",
            f"Via: SIP/2.0/UDP {PHONE_IP}:{self.config.port};branch=z9hG4bK{branch};rport",
            "Max-Forwards: 70",
            f"From: {from_header}",
            f"To: {to_header}",
            f"Call-ID: {call_id}",
            f"CSeq: {cseq} {method}",
            f"Contact: {self.contact}",
            "Content-Length: 0",
        ]
        return ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")


def wait_event(event: threading.Event, label: str, timeout: float = 8.0) -> None:
    if not event.wait(timeout):
        raise TimeoutError(f"timed out waiting for {label}")


def send_media(source: VirtualPhone, target: tuple[str, int], frames: int) -> None:
    for sequence in range(frames):
        packet = struct.pack("!BBHII", 0x80, 0, sequence, sequence * 160, 0x4C41494E) + MEDIA_PAYLOAD
        source.rtp.sendto(packet, target)
        time.sleep(0.02)


def verify_media(phone: VirtualPhone, frames: int, timeout: float = 4.0) -> int:
    count = 0
    deadline = time.monotonic() + timeout
    while count < frames and time.monotonic() < deadline:
        try:
            phone.rtp_packets.get(timeout=0.1)
            count += 1
        except queue.Empty:
            pass
    return count


def resolve_pcscf() -> str:
    expected_ip = os.environ.get("SIP_PCSCF_IP")
    last_error: OSError | None = None
    for _ in range(30):
        try:
            resolved_ip = socket.gethostbyname(PCSCF_DOMAIN)
            if expected_ip and resolved_ip != expected_ip:
                raise RuntimeError(f"P-CSCF DNS resolved to {resolved_ip}, expected {expected_ip}")
            return expected_ip or resolved_ip
        except OSError as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"P-CSCF DNS did not become ready: {last_error}")


def run() -> None:
    pcscf_ip = resolve_pcscf()
    print(f"VIRTUAL_PHONE_PCSCF_DNS_PASS domain={PCSCF_DOMAIN} address={pcscf_ip}", flush=True)
    proxy = (pcscf_ip, 5060)
    phone_a = VirtualPhone(PhoneConfig(PHONE_A_NUMBER, PHONE_A_PASSWORD, 5062, 30000), proxy)
    phone_b = VirtualPhone(PhoneConfig(PHONE_B_NUMBER, PHONE_B_PASSWORD, 5063, 30002), proxy)
    phones = (phone_a, phone_b)
    try:
        for phone in phones:
            phone.start()
        phone_a.register()
        phone_b.register()

        call_id = f"{secrets.token_hex(8)}@virtual-call"
        phone_a.call_id = call_id
        invite = phone_a._request(
            "INVITE",
            sip_uri(PHONE_B_NUMBER),
            1,
            body=make_sdp(PHONE_IP, phone_a.config.media_port, PHONE_A_NUMBER),
            content_type="application/sdp",
        )
        phone_a._send(invite)
        response = phone_a._wait_response("1 INVITE", {200})
        if 180 not in phone_a.provisional_codes.get("1 INVITE", set()):
            raise RuntimeError("caller did not receive SIP 180 Ringing")
        invite_response_headers = parse_headers(response)
        to_header = first(invite_response_headers, "to")
        from_header = first(invite_response_headers, "from")
        phone_a.socket.sendto(
            phone_a.in_dialog_request("ACK", sip_uri(PHONE_B_NUMBER), call_id, 1, from_header, to_header),
            proxy,
        )
        wait_event(phone_b.invite_received, "callee INVITE")
        wait_event(phone_b.ack_received, "callee ACK")
        print("VIRTUAL_CALL_DIALOG_PASS invite=100,180,200 ack=received", flush=True)

        remote_b = media_address(body_of(response))
        send_media(phone_a, remote_b, MEDIA_FRAMES)
        received_b = verify_media(phone_b, MEDIA_FRAMES)
        send_media(phone_b, (PHONE_IP, phone_a.config.media_port), MEDIA_FRAMES)
        received_a = verify_media(phone_a, MEDIA_FRAMES)
        if received_a < MEDIA_FRAMES or received_b < MEDIA_FRAMES:
            raise RuntimeError(f"RTP was not bidirectional: A={received_a}, B={received_b}")
        print(f"VIRTUAL_RTP_PASS direction_a_to_b={received_b} direction_b_to_a={received_a} codec=PCMU payload=silence", flush=True)

        bye = phone_a.in_dialog_request("BYE", sip_uri(PHONE_B_NUMBER), call_id, 2, from_header, to_header)
        phone_a._send(bye)
        phone_a._wait_response("2 BYE", {200})
        wait_event(phone_b.bye_received, "callee BYE")
        print("VIRTUAL_CALL_TEARDOWN_PASS bye=200", flush=True)

        message_id = f"{secrets.token_hex(8)}@virtual-sms"
        phone_a.call_id = message_id
        sms_body = f"OpenLain5G virtual SMS delivery check {secrets.token_hex(4)}"
        message = phone_a._request("MESSAGE", sip_uri(PHONE_B_NUMBER), 1, body=sms_body, content_type="text/plain")
        phone_a._send(message)
        phone_a._wait_response("1 MESSAGE", {200})
        wait_event(phone_b.sms_received, "virtual SMS delivery")
        if phone_b.sms_body != sms_body:
            raise RuntimeError("virtual SMS payload did not match the sent message")
        print("VIRTUAL_SIP_MESSAGE_PASS message=200 recipient=received", flush=True)
        print("VIRTUAL_PHONES_RESULT=PASS registration=2 call=completed teardown=passed rtp=bidirectional sip_message=delivered", flush=True)
    finally:
        for phone in phones:
            phone.close()


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"VIRTUAL_PHONES_RESULT=FAIL reason={exc}", flush=True)
        raise
