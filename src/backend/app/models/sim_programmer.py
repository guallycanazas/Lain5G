from pydantic import BaseModel, Field, field_validator


class SimProgrammerStatus(BaseModel):
    available: bool
    programming_enabled: bool
    readers: list[str] = Field(default_factory=list)
    message: str


class SimReaderRequest(BaseModel):
    reader_index: int = Field(ge=0, le=31)


class SimCardStatus(BaseModel):
    reader: str
    detected: bool
    recognized: bool
    supported: bool
    card: str | None = None
    message: str


class SimProgramRequest(SimReaderRequest):
    mcc: str = Field(min_length=3, max_length=3, pattern=r"^\d{3}$")
    mnc: str = Field(min_length=2, max_length=3, pattern=r"^\d{2,3}$")
    imsi: str = Field(min_length=15, max_length=15, pattern=r"^\d{15}$")
    iccid: str = Field(min_length=19, max_length=19, pattern=r"^\d{19}$")
    ki: str = Field(min_length=32, max_length=32, pattern=r"^[0-9a-fA-F]{32}$")
    opc: str = Field(min_length=32, max_length=32, pattern=r"^[0-9a-fA-F]{32}$")
    adm: str = Field(min_length=1, max_length=8, pattern=r"^\d{1,8}$")
    confirm: bool

    @field_validator("imsi")
    @classmethod
    def plmn_matches_imsi(cls, value: str, info):
        mcc = info.data.get("mcc")
        mnc = info.data.get("mnc")
        if mcc and mnc and not value.startswith(mcc + mnc):
            raise ValueError("IMSI must begin with the selected MCC and MNC")
        return value

    @field_validator("iccid")
    @classmethod
    def valid_iccid_luhn(cls, value: str):
        digits = [int(char) for char in value]
        checksum = 0
        for index, digit in enumerate(reversed(digits)):
            if index % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        if checksum % 10:
            raise ValueError("ICCID check digit is invalid")
        return value

    @field_validator("confirm")
    @classmethod
    def require_explicit_confirmation(cls, value: bool):
        if not value:
            raise ValueError("Confirm the physical SIM write")
        return value


class SimProgramResult(BaseModel):
    success: bool
    reader: str
    card: str
    imsi: str
    iccid: str
    verified_fields: list[str]
    message: str
