#!/usr/bin/env python3
"""Narrow, local-only PC/SC bridge for sysmocom SIM detection and SJS1 programming."""

from __future__ import annotations

import hmac
import json
import os
import re
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from pySim.commands import SimCardCommands
from pySim.legacy.cards import SysmoISIMSJA2, SysmoISIMSJA5, SysmoUSIMSJS1
from pySim.legacy.ts_51_011 import EF
from pySim.transport.pcsc import PcscSimLink
from pySim.utils import enc_iccid, enc_imsi, sanitize_pin_adm
from osmocom.utils import h2b
from smartcard.System import readers as pcsc_readers


TOKEN = os.environ.get("SIM_PROGRAMMER_TOKEN", "")
CARD_MODELS = (SysmoUSIMSJS1, SysmoISIMSJA2, SysmoISIMSJA5)
PROGRAMMABLE_MODEL = SysmoUSIMSJS1.name
HOST = "0.0.0.0"
PORT = 8123


class BridgeError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(message)


def reader_names() -> list[str]:
    try:
        return [str(reader)[:160] for reader in pcsc_readers()]
    except Exception:
        return []


def identify_card(scc: SimCardCommands) -> tuple[str | None, bool]:
    """Return (recognized model name, writable by this bridge)."""
    for card_model in CARD_MODELS:
        try:
            card = card_model.autodetect(scc)
        except Exception:
            card = None
        if card is not None:
            return card.name, card.name == PROGRAMMABLE_MODEL
    return None, False


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("confirm") is not True:
        raise BridgeError(400, "CONFIRMATION_REQUIRED", "Explicit confirmation is required.")
    patterns = {
        "imsi": r"\d{15}",
        "iccid": r"\d{19}",
        "mcc": r"\d{3}",
        "mnc": r"\d{2,3}",
        "ki": r"[0-9a-fA-F]{32}",
        "opc": r"[0-9a-fA-F]{32}",
        "adm": r"\d{1,8}",
    }
    if any(not isinstance(payload.get(name), str) or not re.fullmatch(pattern, payload[name]) for name, pattern in patterns.items()):
        raise BridgeError(400, "INVALID_INPUT", "One or more SIM fields are invalid.")
    if not payload["imsi"].startswith(payload["mcc"] + payload["mnc"]):
        raise BridgeError(400, "INVALID_INPUT", "IMSI does not match the selected MCC and MNC.")
    checksum = 0
    for index, char in enumerate(reversed(payload["iccid"])):
        digit = int(char) * (2 if index % 2 else 1)
        checksum += digit // 10 + digit % 10
    if checksum % 10:
        raise BridgeError(400, "INVALID_INPUT", "ICCID check digit is invalid.")
    if type(payload.get("reader_index")) is not int or not 0 <= payload["reader_index"] < 32:
        raise BridgeError(400, "INVALID_INPUT", "Reader selection is invalid.")


def inspect_card(reader_index: int) -> dict[str, Any]:
    names = reader_names()
    if reader_index >= len(names):
        raise BridgeError(404, "READER_NOT_FOUND", "The selected PC/SC reader is not available.")
    link = None
    try:
        link = PcscSimLink(Namespace(pcsc_dev=reader_index, pcsc_shared=False))
        link.connect()
        scc = SimCardCommands(transport=link)
        model, programmable = identify_card(scc)
        recognized = model is not None
        if programmable:
            message = "sysmoUSIM-SJS1 detected. This model can be programmed by OpenLain5G."
        elif model in {SysmoISIMSJA2.name, SysmoISIMSJA5.name}:
            message = f"{model} detected. OpenLain5G identifies it but does not write this model yet. No card data was changed; its factory ICCID must be preserved."
        elif recognized:
            message = f"{model} detected, but this model is not enabled for writing in OpenLain5G."
        else:
            message = "A card is present, but its model is not recognized by the supported sysmocom profiles. No card data was changed."
        return {
            "reader": names[reader_index],
            "detected": True,
            "recognized": recognized,
            "supported": programmable,
            "card": model,
            "message": message,
        }
    except BridgeError:
        raise
    except Exception:
        raise BridgeError(409, "CARD_NOT_READY", "No readable card was detected in the selected reader.") from None
    finally:
        if link is not None:
            try:
                link.disconnect()
            except Exception:
                pass


def program_card(payload: dict[str, Any]) -> dict[str, Any]:
    validate_payload(payload)
    names = reader_names()
    index = payload["reader_index"]
    if index >= len(names):
        raise BridgeError(404, "READER_NOT_FOUND", "The selected PC/SC reader is not available.")
    link = None
    stage = "card detection"
    changed = False
    try:
        link = PcscSimLink(Namespace(pcsc_dev=index, pcsc_shared=False))
        link.connect()
        scc = SimCardCommands(transport=link)
        model, programmable = identify_card(scc)
        if not programmable:
            if model:
                message = f"{model} is recognized, but OpenLain5G writing is currently enabled only for {PROGRAMMABLE_MODEL}. No card data was changed."
            else:
                message = f"This card model is not recognized. OpenLain5G writing is currently enabled only for {PROGRAMMABLE_MODEL}. No card data was changed."
            raise BridgeError(409, "UNSUPPORTED_CARD", message)
        card = SysmoUSIMSJS1(scc)
        stage = "ADM verification"
        adm = h2b(sanitize_pin_adm(payload["adm"], None))
        if card.verify_adm(adm) != "9000":
            raise BridgeError(403, "ADM_REJECTED", "ADM verification failed. The SIM was not modified; do not guess or retry an uncertain ADM value.")

        def write(field: str, operation) -> None:
            nonlocal stage, changed
            stage = field
            # Once a write APDU is sent, a lost reply can leave card state uncertain.
            changed = True
            sw = operation()
            if sw != "9000":
                raise BridgeError(409, "SIM_WRITE_FAILED", field)

        write("ICCID", lambda: scc.update_binary(EF["ICCID"], enc_iccid(payload["iccid"]))[1])
        write("Ki", lambda: scc.update_binary(["3f00", "7f20", "00ff"], payload["ki"].lower())[1])
        write("OPc", lambda: scc.update_binary(["3f00", "7f20", "00f7"], "01" + payload["opc"].lower())[1])
        write("IMSI", lambda: scc.update_binary(EF["IMSI"], enc_imsi(payload["imsi"]))[1])
        write("MNC length", lambda: card.update_ad(mnc=payload["mnc"]))

        stage = "read-back verification"
        read_iccid, iccid_sw = card.read_iccid()
        read_imsi, imsi_sw = card.read_imsi()
        scc.select_path(["3f00", "7f20"])
        read_ki, ki_sw = scc.read_binary("00ff")
        read_opc, opc_sw = scc.read_binary("00f7")
        verified = (
            iccid_sw == "9000" and read_iccid == payload["iccid"]
            and imsi_sw == "9000" and read_imsi == payload["imsi"]
            and ki_sw == "9000" and hmac.compare_digest(read_ki.lower(), payload["ki"].lower())
            and opc_sw == "9000" and hmac.compare_digest(read_opc.lower(), "01" + payload["opc"].lower())
        )
        if not verified:
            raise BridgeError(409, "SIM_VERIFY_FAILED", "Card read-back did not match all programmed fields.")

        return {
            "success": True,
            "reader": names[index],
            "card": "sysmoUSIM-SJS1",
            "imsi": payload["imsi"],
            "iccid": payload["iccid"],
            "verified_fields": ["ICCID", "Ki", "OPc", "IMSI", "MNC length"],
            "message": "SIM programming and read-back verification completed.",
        }
    except BridgeError as exc:
        if changed and exc.code in {"SIM_WRITE_FAILED", "SIM_VERIFY_FAILED"}:
            raise BridgeError(exc.status, exc.code, f"Operation stopped during {exc.message}. The SIM may be partially programmed; inspect it before retrying.") from None
        raise
    except Exception:
        message = f"Operation stopped during {stage}."
        if changed:
            message += " The SIM may be partially programmed; inspect it before retrying."
        raise BridgeError(409, "SIM_OPERATION_FAILED", message) from None
    finally:
        if link is not None:
            try:
                link.disconnect()
            except Exception:
                pass


class Handler(BaseHTTPRequestHandler):
    server_version = "OpenLainSIMBridge"

    def log_message(self, _format: str, *args: Any) -> None:
        # Never write request data, path parameters, or APDU/card content to logs.
        return

    def send_json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self) -> bool:
        if not TOKEN:
            return False
        supplied = self.headers.get("Authorization", "").removeprefix("Bearer ")
        return hmac.compare_digest(supplied, TOKEN)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        if self.path != "/readers":
            self.send_json(404, {"code": "NOT_FOUND", "message": "Unknown endpoint."})
            return
        if not self.authorized():
            self.send_json(401, {"code": "UNAUTHORIZED", "message": "Access denied."})
            return
        self.send_json(200, {"readers": reader_names()})

    def do_POST(self) -> None:  # noqa: N802
        if not self.authorized():
            self.send_json(401, {"code": "UNAUTHORIZED", "message": "Access denied."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 4096:
                raise BridgeError(413, "INVALID_REQUEST", "Request size is invalid.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise BridgeError(400, "INVALID_REQUEST", "Request body is invalid.")
            if self.path == "/inspect":
                index = payload.get("reader_index")
                if type(index) is not int or not 0 <= index < 32:
                    raise BridgeError(400, "INVALID_INPUT", "Reader selection is invalid.")
                self.send_json(200, inspect_card(index))
                return
            if self.path == "/program":
                self.send_json(200, program_card(payload))
                return
            raise BridgeError(404, "NOT_FOUND", "Unknown endpoint.")
        except BridgeError as exc:
            self.send_json(exc.status, {"code": exc.code, "message": exc.message})
        except Exception:
            self.send_json(400, {"code": "INVALID_REQUEST", "message": "Request body is invalid."})


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("SIM_PROGRAMMER_TOKEN is required")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
