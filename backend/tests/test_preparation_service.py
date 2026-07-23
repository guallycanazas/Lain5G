from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.app.models.deployment import CommandResult
from backend.app.services.image_catalog import MONGO_IMAGE, PROFILE_IMAGES
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


def test_image_catalog_covers_every_configurable_profile():
    assert set(PROFILE_IMAGES) == ProfileConfigService.PROFILE_IDS


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
