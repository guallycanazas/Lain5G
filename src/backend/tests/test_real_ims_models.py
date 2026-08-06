import pytest
from pydantic import ValidationError

from backend.app.models.real_ims import PLMN, RealIMSSubscriber


VALID = {
    "imsi": "001010000000001",
    "msisdn": "+15551234567",
    "ki": "00112233445566778899aabbccddeeff",
    "opc": "ffeeddccbbaa99887766554433221100",
}


def test_real_ims_subscriber_normalizes_valid_values():
    subscriber = RealIMSSubscriber(**VALID, amf="80ab", sqn=0xFFFFFFFFFFFF, apn_ims="IMS.MNC001")

    assert subscriber.msisdn == "15551234567"
    assert subscriber.ki == VALID["ki"].upper()
    assert subscriber.opc == VALID["opc"].upper()
    assert subscriber.amf == "80AB"
    assert subscriber.sqn_hex == "FFFFFFFFFFFF"
    assert subscriber.apn_ims == "ims.mnc001"
    assert "ki" not in subscriber.model_dump()
    assert "opc" not in subscriber.model_dump()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("imsi", "00101"),
        ("imsi", "00101000000000x"),
        ("msisdn", "+12"),
        ("msisdn", "1555 12345"),
        ("ki", "0" * 31),
        ("opc", "z" * 32),
        ("amf", "800"),
        ("sqn", 0x1000000000000),
        ("apn_internet", "bad..apn"),
        ("apn_ims", "-ims"),
    ],
)
def test_real_ims_subscriber_rejects_invalid_fields(field, value):
    payload = {**VALID, field: value}
    with pytest.raises(ValidationError):
        RealIMSSubscriber(**payload)


@pytest.mark.parametrize(("mcc", "mnc"), [("01", "01"), ("001", "1"), ("abc", "001"), ("001", "0001")])
def test_plmn_is_strict(mcc, mnc):
    with pytest.raises(ValidationError):
        PLMN(mcc=mcc, mnc=mnc)
