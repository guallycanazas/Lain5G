from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


ConnectionStatus = Literal["connected", "disconnected", "timeout", "misconfigured", "error", "dry_run"]

IMSI_RE = re.compile(r"^\d{5,15}$")
MSISDN_RE = re.compile(r"^\d{5,20}$")
HEX32_RE = re.compile(r"^[0-9a-fA-F]{32}$")
AMF_RE = re.compile(r"^[0-9a-fA-F]{4}$")
SQN_RE = re.compile(r"^[0-9a-fA-F]{12}$")
SD_RE = re.compile(r"^[0-9a-fA-F]{6}$")
DNN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,62}$")
MASKED_SECRET_VALUES = {"********", "[REDACTED]", "redacted"}


class Open5GSConnectionStatus(BaseModel):
    status: ConnectionStatus
    database: str
    collection: str
    server: str
    latency_ms: int | None = None
    checked_at: datetime
    message: str | None = None


class SubscriberSecretInput(BaseModel):
    k: str | None = None
    op: str | None = None
    opc: str | None = None
    amf: str | None = "8000"
    sqn: str | None = "000000000001"

    @field_validator("k", "op", "opc", mode="before")
    @classmethod
    def normalize_secret(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if stripped in MASKED_SECRET_VALUES or set(stripped) == {"*"}:
                raise ValueError("masked secrets are not accepted as new values")
            if not HEX32_RE.fullmatch(stripped):
                raise ValueError("secret must be exactly 32 hexadecimal characters")
            return stripped.upper()
        raise ValueError("secret must be a string")

    @field_validator("amf", mode="before")
    @classmethod
    def normalize_amf(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if not AMF_RE.fullmatch(stripped):
                raise ValueError("amf must be exactly 4 hexadecimal characters")
            return stripped.upper()
        raise ValueError("amf must be a string")

    @field_validator("sqn", mode="before")
    @classmethod
    def normalize_sqn(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if set(stripped) == {"*"}:
                raise ValueError("masked sqn is not accepted as a new value")
            if not SQN_RE.fullmatch(stripped):
                raise ValueError("sqn must be exactly 12 hexadecimal characters")
            return stripped.upper()
        raise ValueError("sqn must be a string")

    @model_validator(mode="after")
    def validate_secret_combination(self) -> SubscriberSecretInput:
        if self.op and self.opc:
            raise ValueError("provide either OP or OPc, not both")
        return self


class SubscriberSliceInput(BaseModel):
    sst: int = Field(default=1, ge=1, le=255)
    sd: str | None = "000001"

    @field_validator("sd", mode="before")
    @classmethod
    def normalize_sd(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if not SD_RE.fullmatch(stripped):
                raise ValueError("sd must be exactly 6 hexadecimal characters")
            return stripped.upper()
        raise ValueError("sd must be a string")


class SubscriberCreate(BaseModel):
    imsi: str
    msisdn: str | None = None
    security: SubscriberSecretInput
    slice: SubscriberSliceInput = Field(default_factory=SubscriberSliceInput)
    dnn: str = "internet"

    @field_validator("imsi", mode="before")
    @classmethod
    def validate_imsi(cls, value: object) -> str:
        if not isinstance(value, str) or not IMSI_RE.fullmatch(value):
            raise ValueError("imsi must contain 5 to 15 digits")
        return value

    @field_validator("msisdn", mode="before")
    @classmethod
    def validate_msisdn(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if not MSISDN_RE.fullmatch(stripped):
                raise ValueError("msisdn must contain 5 to 20 digits")
            return stripped
        raise ValueError("msisdn must be a string")

    @field_validator("dnn", mode="before")
    @classmethod
    def validate_dnn(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("dnn must be a string")
        stripped = value.strip()
        if not stripped or " " in stripped or not DNN_RE.fullmatch(stripped):
            raise ValueError("dnn must be a safe non-empty name without spaces")
        return stripped.lower()

    @model_validator(mode="after")
    def validate_create_secrets(self) -> SubscriberCreate:
        if not self.security.k:
            raise ValueError("K is required")
        if not self.security.op and not self.security.opc:
            raise ValueError("OP or OPc is required")
        if not self.security.amf:
            raise ValueError("AMF is required")
        if not self.security.sqn:
            raise ValueError("SQN is required")
        return self


class SubscriberUpdate(BaseModel):
    msisdn: str | None = None
    security: SubscriberSecretInput | None = None
    slice: SubscriberSliceInput | None = None
    dnn: str | None = None

    model_config = ConfigDict(extra="forbid")

    _validate_msisdn = field_validator("msisdn", mode="before")(SubscriberCreate.validate_msisdn.__func__)
    _validate_dnn = field_validator("dnn", mode="before")(SubscriberCreate.validate_dnn.__func__)

    @model_validator(mode="before")
    @classmethod
    def reject_imsi_change(cls, value: Any) -> Any:
        if isinstance(value, dict) and "imsi" in value:
            raise ValueError("imsi cannot be changed by update; use clone")
        return value


class SubscriberClone(BaseModel):
    new_imsi: str
    new_msisdn: str | None = None

    _validate_new_imsi = field_validator("new_imsi", mode="before")(SubscriberCreate.validate_imsi.__func__)
    _validate_new_msisdn = field_validator("new_msisdn", mode="before")(SubscriberCreate.validate_msisdn.__func__)


class SubscriberSecurityRedacted(BaseModel):
    k_configured: bool
    op_configured: bool
    opc_configured: bool
    amf: str | None = None
    sqn: str | None = None


class SubscriberSummary(BaseModel):
    imsi: str
    msisdn: str | None = None
    dnn: str | None = None
    sst: int | None = None
    sd: str | None = None
    security: SubscriberSecurityRedacted


class SubscriberDetail(SubscriberSummary):
    checked_at: datetime
    note: str = "A subscriber record in Open5GS does not establish that the UE authenticated successfully."


class SubscriberListResponse(BaseModel):
    items: list[SubscriberSummary]
    total: int
    limit: int
    offset: int


class SubscriberValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


class SubscriberOperationResponse(BaseModel):
    subscriber: SubscriberDetail | None = None
    dry_run: bool = False
    persisted: bool = True
    message: str
