from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.app.models.deployment import CommandResult
from backend.app.services.image_catalog import MONGO_IMAGE, PROFILE_IMAGES, PUBLIC_PROFILE_IDS
from backend.app.services.preparation_service import PreparationError, PreparationService
from backend.app.services.profile_config_service import ProfileConfigService
from backend.app.settings import Settings


class FakeCommands:
    def __init__(self, installed: set[str] | None = None):
        self.installed = installed or set()
        self.commands: list[list[str]] = []

    def execute_command(self, command: list[str], **kwargs) -> CommandResult:
        self.commands.append(command)
        exit_code = 0
        if command[:3] == ["docker", "image", "inspect"]:
            exit_code = 0 if command[3] in self.installed else 1
        elif command[:2] == ["docker", "pull"]:
            self.installed.add(command[2])
        elif command[:2] == ["docker", "tag"]:
            self.installed.add(command[3])
        now = datetime.now(UTC)
        return CommandResult(
            command=command,
            cwd=".",
            exit_code=exit_code,
            stdout="ok" if exit_code == 0 else "",
            stderr="" if exit_code == 0 else "missing",
            started_at=now,
            finished_at=now,
            duration_ms=0,
        )


def service(tmp_path: Path, commands: FakeCommands) -> PreparationService:
    return PreparationService(Settings(project_root=tmp_path, image_pull_enabled=True), commands)  # type: ignore[arg-type]


def test_image_catalog_covers_every_configurable_profile(tmp_path: Path):
    assert set(PROFILE_IMAGES) == ProfileConfigService.PROFILE_IDS

    report = service(tmp_path, FakeCommands()).report()
    assert [profile.profile for profile in report.profiles] == list(PUBLIC_PROFILE_IDS)


def test_pull_uses_only_fixed_pull_and_tag_commands(tmp_path: Path):
    commands = FakeCommands()
    result = service(tmp_path, commands).pull("4g-lte-sim")

    assert result.profile.ready is True
    assert result.pulled == [
        "gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c",
        "gually/lain5g-srsran4g-sim:23.11-lain1@sha256:7ec771cf70e77f699283017b02bbe6311fd377047109dc952c2c18ebae1e2ced",
        MONGO_IMAGE,
    ]
    executed = [" ".join(command) for command in commands.commands]
    assert "docker pull gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c" in executed
    assert "docker tag gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c lain5g-lab/open5gs:local" in executed
    assert not any(token in command for command in executed for token in (" build ", " push ", " compose ", " prune "))


def test_unknown_profile_is_rejected_before_docker(tmp_path: Path):
    commands = FakeCommands()
    with pytest.raises(PreparationError) as exc:
        service(tmp_path, commands).profile_status("../../otro")
    assert exc.value.code == "IMAGE_PROFILE_NOT_FOUND"
    assert commands.commands == []


def test_image_pull_specific_opt_in_is_required(tmp_path: Path):
    commands = FakeCommands()
    settings = Settings(project_root=tmp_path, mutating_operations_enabled=True, image_pull_enabled=False)

    with pytest.raises(PreparationError) as exc:
        PreparationService(settings, commands).pull("5g-sa")

    assert exc.value.code == "IMAGE_PULL_DISABLED"
    assert commands.commands == []


def test_core_only_does_not_require_the_rf_access_image(tmp_path: Path):
    commands = FakeCommands({"lain5g-lab/open5gs:local", MONGO_IMAGE})
    status = service(tmp_path, commands).profile_status("5g-sa-x310", core_only=True)
    assert status.ready is True
    assert all(image.local_image != "lain5g-lab/srsranproject-uhd:local" for image in status.images)


@pytest.mark.parametrize(
    ("profile", "directory", "requires_ims_password"),
    (
        ("4g-lte-sim", "deployments/4g-volte/common", False),
        ("4g-volte-sim", "deployments/4g-volte/common", True),
        ("5g-sa", "deployments/5g-sa", False),
        ("5g-vonr-sim", "deployments/5g-vonr", True),
    ),
)
def test_prepare_environment_supports_every_software_scenario(
    tmp_path: Path,
    profile: str,
    directory: str,
    requires_ims_password: bool,
):
    environment_dir = tmp_path / directory
    environment_dir.mkdir(parents=True)
    template = "SUBSCRIBER_KEY=\nSUBSCRIBER_OPC=\n"
    if requires_ims_password:
        template += "IMS_AUTH_PASSWORD=\n"
    (environment_dir / ".env.example").write_text(template, encoding="utf-8")

    target = service(tmp_path, FakeCommands()).prepare_environment(profile)
    values = dict(line.split("=", 1) for line in target.read_text(encoding="utf-8").splitlines())

    assert len(values["SUBSCRIBER_KEY"]) == 32
    assert len(values["SUBSCRIBER_OPC"]) == 32
    assert bool(values.get("IMS_AUTH_PASSWORD")) is requires_ims_password
    assert target.stat().st_mode & 0o777 == 0o600


def test_prepare_environment_preserves_existing_quoted_secret(tmp_path: Path):
    environment_dir = tmp_path / "deployments/5g-vonr"
    environment_dir.mkdir(parents=True)
    (environment_dir / ".env.example").write_text(
        "SUBSCRIBER_KEY=\nSUBSCRIBER_OPC=\nIMS_AUTH_PASSWORD=\n",
        encoding="utf-8",
    )
    target = environment_dir / ".env"
    target.write_text(
        "SUBSCRIBER_KEY=\nSUBSCRIBER_OPC=\nIMS_AUTH_PASSWORD='secret value'\n",
        encoding="utf-8",
    )

    service(tmp_path, FakeCommands()).prepare_environment("5g-vonr")

    assert "IMS_AUTH_PASSWORD='secret value'" in target.read_text(encoding="utf-8")


def test_prepare_environment_rejects_symlink_target(tmp_path: Path):
    environment_dir = tmp_path / "deployments/5g-sa"
    environment_dir.mkdir(parents=True)
    (environment_dir / ".env.example").write_text("SUBSCRIBER_KEY=\nSUBSCRIBER_OPC=\n", encoding="utf-8")
    (environment_dir / ".env").symlink_to(tmp_path / "outside")

    with pytest.raises(PreparationError) as exc:
        service(tmp_path, FakeCommands()).prepare_environment("5g-sa")

    assert exc.value.code == "ENVIRONMENT_PREPARATION_FAILED"
    assert "outside" not in exc.value.message


def test_concurrent_environment_preparation_reuses_one_generation(tmp_path: Path, monkeypatch):
    environment_dir = tmp_path / "deployments/5g-sa"
    environment_dir.mkdir(parents=True)
    (environment_dir / ".env.example").write_text("SUBSCRIBER_KEY=\nSUBSCRIBER_OPC=\n", encoding="utf-8")
    preparation = service(tmp_path, FakeCommands())
    calls = 0

    def token_hex(_length: int) -> str:
        nonlocal calls
        calls += 1
        time.sleep(0.02)
        return f"{calls:032x}"

    monkeypatch.setattr("backend.app.services.scenario_environment.secrets.token_hex", token_hex)
    with ThreadPoolExecutor(max_workers=2) as executor:
        targets = list(executor.map(preparation.prepare_environment, ("5g-sa", "5g-sa")))

    assert targets[0] == targets[1]
    assert calls == 2
