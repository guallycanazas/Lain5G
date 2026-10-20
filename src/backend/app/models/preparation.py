from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PreparationCheck(BaseModel):
    id: str
    label: str
    status: Literal["PASS", "WARNING", "FAIL"]
    detail: str


class ComponentImageStatus(BaseModel):
    local_image: str
    source_image: str
    description: str
    installed: bool


class ProfileComponentStatus(BaseModel):
    profile: str
    name: str
    rf_capable: bool
    core_only: bool
    ready: bool
    installed_count: int
    total_count: int
    images: list[ComponentImageStatus]


class PreparationReport(BaseModel):
    checked_at: datetime
    ready: bool
    diagnostics: list[PreparationCheck]
    profiles: list[ProfileComponentStatus]


class ComponentPullRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    core_only: bool = False


class ComponentPullResponse(BaseModel):
    profile: ProfileComponentStatus
    pulled: list[str]
    message: str


class ComponentPullImageProgress(BaseModel):
    local_image: str
    source_image: str
    description: str
    reason: str = ""
    state: Literal["pending", "pulling", "tagging", "succeeded", "failed"] = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class ComponentPullJob(BaseModel):
    job_id: str
    scope: str
    core_only: bool
    state: Literal["queued", "running", "succeeded", "failed"]
    images: list[ComponentPullImageProgress]
    current_image: str | None = None
    current_index: int = 0
    completed_count: int = 0
    total_count: int = 0
    overall_percent: int = 0
    pulled: list[str] = Field(default_factory=list)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None


class InstallationStep(BaseModel):
    name: str
    reason: str
    status: Literal["pending", "running", "succeeded", "failed", "skipped"]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    exit_code: int | None = None
    message: str | None = None


class InstallationEnvironment(BaseModel):
    host_os: str
    host_architecture: str
    machine_type: str
    detection_method: str
    runtime: str
    runtime_os: str
    runtime_architecture: str


class InstallationRecord(BaseModel):
    id: str
    kind: Literal["bootstrap", "component_download"]
    scope: str
    status: Literal["running", "succeeded", "failed", "dry_run", "partial"]
    reason: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    environment: InstallationEnvironment
    installed_components: list[str] = Field(default_factory=list)
    steps: list[InstallationStep] = Field(default_factory=list)
    log_available: bool = False
