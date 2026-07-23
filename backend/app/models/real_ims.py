from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Mode = Literal["4g", "5g"]
HEX_32 = re.compile(r"^[0-9A-Fa-f]{32}$")
HEX_4 = re.compile(r"^[0-9A-Fa-f]{4}$")
APN_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


class RealIMSModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class PLMN(RealIMSModel):
    mcc: str = Field(default="001", pattern=r"^[0-9]{3}$")
    mnc: str = Field(default="01", pattern=r"^[0-9]{2,3}$")


class RealIMSSubscriber(RealIMSModel):
    imsi: str
    msisdn: str
    ki: str = Field(repr=False, exclude=True)
    opc: str = Field(repr=False, exclude=True)
    amf: str = "8000"
    sqn: int = Field(default=0, ge=0, le=0xFFFFFFFFFFFF, strict=True)
    apn_internet: str = "internet"
    apn_ims: str = "ims"
    enabled: bool = True

    @field_validator("imsi")
    @classmethod
    def validate_imsi(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9]{14,15}", value):
            raise ValueError("IMSI must contain 14 or 15 digits")
        return value

    @field_validator("msisdn")
    @classmethod
    def validate_msisdn(cls, value: str) -> str:
        normalized = value[1:] if value.startswith("+") else value
        if not re.fullmatch(r"[0-9]{5,15}", normalized):
            raise ValueError("MSISDN must contain 5 to 15 digits, optionally prefixed by +")
        return normalized

    @field_validator("ki", "opc")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if not HEX_32.fullmatch(value):
            raise ValueError("subscriber key must contain exactly 32 hexadecimal characters")
        return value.upper()

    @field_validator("amf")
    @classmethod
    def validate_amf(cls, value: str) -> str:
        if not HEX_4.fullmatch(value):
            raise ValueError("AMF must contain exactly 4 hexadecimal characters")
        return value.upper()

    @field_validator("apn_internet", "apn_ims")
    @classmethod
    def validate_apn(cls, value: str) -> str:
        if len(value) > 100 or any(not APN_LABEL.fullmatch(label) for label in value.split(".")):
            raise ValueError("APN/DNN must be a valid dot-separated network name")
        return value.lower()

    @property
    def sqn_hex(self) -> str:
        return f"{self.sqn:012X}"


class RealIMSAction(RealIMSModel):
    mode: Mode
    execute: bool = False


class RealIMSStartRequest(RealIMSAction, PLMN):
    pass


class RealIMSStopRequest(RealIMSAction):
    pass


class RealIMSImagesRequest(RealIMSModel):
    execute: bool = False
    force: bool = False


class RealIMSProvisionRequest(RealIMSAction, PLMN):
    subscriber: RealIMSSubscriber

    @model_validator(mode="after")
    def validate_subscriber_plmn(self) -> "RealIMSProvisionRequest":
        if not self.subscriber.imsi.startswith(f"{self.mcc}{self.mnc}"):
            raise ValueError("subscriber IMSI does not match the requested MCC/MNC")
        return self


class ResourceResult(RealIMSModel):
    resource: str
    resource_id: int | None = None
    action: Literal["created", "updated", "verified"]
    status: Literal["PASS", "FAIL"] = "PASS"


class PyHSSProvisioningReport(RealIMSModel):
    status: Literal["PASS", "FAIL"]
    imsi: str
    resources: list[ResourceResult]
    api_version: str = "pyHSS-1.0.2"


class RealIMSCheck(RealIMSModel):
    id: str
    status: Literal["PASS", "WARNING", "FAIL"]
    message: str
    evidence: dict[str, object] = Field(default_factory=dict)


class RealIMSStatusReport(RealIMSModel):
    mode: Mode
    status: Literal["PASS", "WARNING", "FAIL"]
    checks: list[RealIMSCheck]


class RealIMSSubscriberSummary(RealIMSModel):
    imsi: str
    msisdn: str
    impi: str
    impu: str
    domain: str
    scscf: str | None = None
    enabled: bool
    apns: list[str]
    open5gs_present: bool
    pyhss_present: bool


class RealIMSSubscriberList(RealIMSModel):
    mode: Mode
    count: int
    subscribers: list[RealIMSSubscriberSummary]
    secrets_redacted: Literal[True] = True
