from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_deployment_service, get_run_service, get_validation_service, settings_dependency
from backend.app.main import create_app
from backend.app.services.command_service import CommandService
from backend.app.services.deployment_service import DeploymentService
from backend.app.services.run_service import RunService
from backend.app.services.validation_service import ValidationService
from backend.app.settings import Settings


FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    scripts_dir = root / "deployments" / "5g-sa" / "scripts"
    runs_dir = root / "runs"
    scripts_dir.mkdir(parents=True)
    shutil.copytree(FIXTURES / "runs", runs_dir)
    for script in (FIXTURES / "scripts").iterdir():
        target = scripts_dir / script.name
        shutil.copy2(script, target)
        target.chmod(0o755)
    (root / "deployments" / "5g-sa" / ".env").write_text("LAIN5G_DRY_RUN=true\n", encoding="utf-8")
    return root


@pytest.fixture
def dry_settings(project_root: Path) -> Settings:
    return Settings(
        project_root=project_root,
        dry_run=True,
        mutating_operations_enabled=False,
        command_timeout=1,
        log_tail_lines=100,
        max_output_chars=1000,
    )


@pytest.fixture
def real_settings(project_root: Path) -> Settings:
    return Settings(
        project_root=project_root,
        dry_run=False,
        mutating_operations_enabled=True,
        command_timeout=1,
        log_tail_lines=100,
        max_output_chars=1000,
    )


@pytest.fixture
def run_service(dry_settings: Settings) -> RunService:
    return RunService(dry_settings)


@pytest.fixture
def validation_service(run_service: RunService) -> ValidationService:
    return ValidationService(run_service)


@pytest.fixture
def command_service(dry_settings: Settings) -> CommandService:
    return CommandService(dry_settings)


@pytest.fixture
def deployment_service(dry_settings: Settings, command_service: CommandService, run_service: RunService, validation_service: ValidationService) -> DeploymentService:
    return DeploymentService(dry_settings, command_service, run_service, validation_service)


@pytest.fixture
def client(dry_settings: Settings, deployment_service: DeploymentService, run_service: RunService, validation_service: ValidationService) -> TestClient:
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: dry_settings
    app.dependency_overrides[get_deployment_service] = lambda: deployment_service
    app.dependency_overrides[get_run_service] = lambda: run_service
    app.dependency_overrides[get_validation_service] = lambda: validation_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
