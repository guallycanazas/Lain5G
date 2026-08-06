from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunSummary(BaseModel):
    run_id: str
    scenario: str | None = None
    deployment_path: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    status: str | None = None
    git_commit: str | None = None
    validated_claims: list[str] = Field(default_factory=list)


class RunDetail(BaseModel):
    run_id: str
    metadata: dict[str, Any]
    validation: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    logs: list[str] = Field(default_factory=list)
    loaded_at: datetime
