from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ValidationState = Literal["PASS", "FAIL", "WARNING", "NOT_TESTED"]


class ValidationCheck(BaseModel):
    id: str
    status: ValidationState
    detail: str | None = None


class ValidationReport(BaseModel):
    run_id: str | None = None
    scenario: str
    status: ValidationState
    validation: dict[str, ValidationState]
    checks: list[ValidationCheck] = Field(default_factory=list)
    checked_at: datetime | None = None
