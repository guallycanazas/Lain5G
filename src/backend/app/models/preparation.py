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


class DockerHostInfo(BaseModel):
    name: str | None = None
    operating_system: str | None = None
    os_type: str | None = None
    os_version: str | None = None
    architecture: str | None = None
    manufacturer: str | None = None
    product_name: str | None = None
    firmware_vendor: str | None = None
    firmware_version: str | None = None
    board_name: str | None = None
    virtualization: str | None = None
    cpu_model: str | None = None
    physical_cores: int | None = None
    kernel_version: str | None = None
    docker_version: str | None = None
    storage_driver: str | None = None
    docker_root_dir: str | None = None
    cgroup_driver: str | None = None
    cgroup_version: str | None = None
    cpus: int | None = None
    memory_bytes: int | None = None
    swap_bytes: int | None = None
    containers_total: int | None = None
    containers_running: int | None = None
    containers_paused: int | None = None
    containers_stopped: int | None = None
    images_count: int | None = None
    workspace_disk_total_bytes: int | None = None
    workspace_disk_free_bytes: int | None = None


class PreparationReport(BaseModel):
    checked_at: datetime
    ready: bool
    diagnostics: list[PreparationCheck]
    profiles: list[ProfileComponentStatus]
    docker_host: DockerHostInfo | None = None


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
    state: Literal["pending", "pulling", "tagging", "succeeded", "failed"] = "pending"
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
