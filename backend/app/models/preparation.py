from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


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
