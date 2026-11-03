from __future__ import annotations

import os
import queue
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("IMS_DOMAIN", "ims.mnc001.mcc001.3gppnetwork.org")
sys.path.insert(0, str(ROOT / "images" / "ims-sip"))

from sip_virtual_phones import VirtualPhone  # noqa: E402


def test_virtual_phone_accepts_delayed_ringing_after_final_udp_response():
    phone = object.__new__(VirtualPhone)
    phone.responses = queue.Queue()
    phone.provisional_codes = {}
    phone.responses.put("SIP/2.0 180 Ringing\r\nCSeq: 1 INVITE\r\n\r\n")

    phone._wait_provisional("1 INVITE", 180, timeout=0.1)

    assert phone.provisional_codes["1 INVITE"] == {180}


def test_virtual_phone_waits_for_delayed_ringing_after_final_response_was_consumed():
    phone = object.__new__(VirtualPhone)
    phone.responses = queue.Queue()
    phone.provisional_codes = {}
    phone.responses.put("SIP/2.0 200 OK\r\nCSeq: 1 INVITE\r\n\r\n")
    phone.responses.put("SIP/2.0 180 Ringing\r\nCSeq: 1 INVITE\r\n\r\n")

    final = phone._wait_response("1 INVITE", {200})
    phone._wait_provisional("1 INVITE", 180, timeout=0.1)

    assert "200 OK" in final
    assert phone.provisional_codes["1 INVITE"] == {180}
