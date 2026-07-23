from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..version import VERSION


DeploymentState = Literal["running", "stopped", "partial", "error", "unknown", "dry_run"]


class ErrorDetail(BaseModel):
    code: str
    message: str
    exit_code: int | None = None
    stderr: str | None = None
    active_scenario: str | None = None


class ErrorResponse(BaseModel):
    detail: ErrorDetail


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "lain5g-lab-backend"
    version: str = VERSION
    dry_run: bool


class CommandResult(BaseModel):
    command: list[str]
    cwd: str
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    timed_out: bool = False
    dry_run: bool = False


class ContainerStatus(BaseModel):
    name: str
    service: str | None = None
    status: str
    running: bool


class DeploymentSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    path: str
    status: DeploymentState
    mode: str = "simulation"
    supported_actions: list[str]
    validation_checks: list[str] = Field(default_factory=list)
    rf_capable: bool = False
    components: list[str] = Field(default_factory=list)


class DeploymentStatus(BaseModel):
    id: str
    status: DeploymentState
    containers: list[ContainerStatus] = Field(default_factory=list)
    checked_at: datetime
    command: CommandResult
    output: str = ""


class DeploymentActionResponse(BaseModel):
    id: str
    action: str
    status: DeploymentState
    command: CommandResult
    message: str


class RfAcknowledgements(BaseModel):
    legal_authorization_valid: bool = False
    isolation_and_attenuation_verified: bool = False
    channel_and_gain_reviewed: bool = False
    emergency_stop_accessible: bool = False


class RfStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execute: bool = False
    confirmation_phrase: str = ""
    operator_note: str = Field(default="", max_length=240)
    requested_duration_seconds: int = Field(default=60, ge=1, le=600)
    acknowledgements: RfAcknowledgements = Field(default_factory=RfAcknowledgements)

    @field_validator("operator_note")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(character in value for character in ("\x00", "\r", "\n")):
            raise ValueError("Operator note contains unsupported control characters")
        return value

    @model_validator(mode="after")
    def require_execution_guards(self) -> "RfStartRequest":
        if self.execute and not all(self.acknowledgements.model_dump().values()):
            raise ValueError("All RF safety acknowledgements are required")
        if self.execute and len(self.operator_note.strip()) < 3:
            raise ValueError("An operator note is required for RF execution")
        return self


class LogsResponse(BaseModel):
    id: str
    container: str | None = None
    tail: int
    command: CommandResult


class RawPayload(BaseModel):
    data: dict[str, Any]
