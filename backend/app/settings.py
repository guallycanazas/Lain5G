import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    project_root: Path = Field(default_factory=default_project_root, alias="LAIN5G_PROJECT_ROOT")
    scenario: str = Field(default="5g-sa", alias="LAIN5G_SCENARIO")
    dry_run: bool = Field(default=False, alias="LAIN5G_DRY_RUN")
    mutating_operations_enabled: bool = Field(default=False, alias="LAIN5G_MUTATING_OPERATIONS_ENABLED")
    command_timeout: int = Field(default=300, ge=1, le=3600, alias="LAIN5G_COMMAND_TIMEOUT")
    image_pull_timeout: int = Field(default=3600, ge=30, le=7200, alias="LAIN5G_IMAGE_PULL_TIMEOUT")
    log_tail_lines: int = Field(default=500, ge=1, le=5000, alias="LAIN5G_LOG_TAIL_LINES")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="LAIN5G_CORS_ORIGINS",
    )
    max_output_chars: int = Field(default=20000, ge=1000, le=50000, alias="LAIN5G_MAX_OUTPUT_CHARS")
    open5gs_mongo_uri: str = Field(default="mongodb://mongo:27017/open5gs", alias="LAIN5G_OPEN5GS_MONGO_URI")
    open5gs_mongo_database: str = Field(default="open5gs", alias="LAIN5G_OPEN5GS_MONGO_DATABASE")
    open5gs_subscriber_collection: str = Field(default="subscribers", alias="LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION")
    subscriber_secrets_visible: bool = Field(default=False, alias="LAIN5G_SUBSCRIBER_SECRETS_VISIBLE")
    subscriber_operation_timeout: int = Field(default=15, ge=1, le=120, alias="LAIN5G_SUBSCRIBER_OPERATION_TIMEOUT")
    open5gs_docker_network: str = Field(default="lain5g-lab-5g-sa-core", alias="LAIN5G_OPEN5GS_DOCKER_NETWORK")
    rf_web_control_enabled: bool = Field(default=False, alias="LAIN5G_RF_WEB_CONTROL_ENABLED")
    image_pull_enabled: bool = Field(default=False, alias="LAIN5G_IMAGE_PULL_ENABLED")

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @field_validator("project_root")
    @classmethod
    def resolve_project_root(cls, value: Path) -> Path:
        return value.expanduser().resolve()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value  # type: ignore[return-value]

    @field_validator("open5gs_docker_network")
    @classmethod
    def validate_docker_network(cls, value: str) -> str:
        value = value.strip()
        if value and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
            raise ValueError("Docker network name contains unsupported characters")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
