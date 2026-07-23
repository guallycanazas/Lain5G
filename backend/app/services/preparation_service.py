from __future__ import annotations

import shutil
import threading
from datetime import UTC, datetime

from ..models.preparation import ComponentImageStatus, ComponentPullResponse, PreparationCheck, PreparationReport, ProfileComponentStatus
from ..settings import Settings
from .command_service import CommandService
from .image_catalog import IMAGE_CATALOG, PROFILE_IMAGES, RF_ACCESS_IMAGES, required_images


PROFILE_NAMES = {
    "4g-lte-sim": "4G LTE simulation",
    "4g-volte-sim": "4G VoLTE simulation",
    "4g-lte-x310": "4G LTE/VoLTE X310",
    "5g-sa": "5G SA simulation",
    "5g-sa-x310": "5G SA X310",
    "5g-nsa-x310": "5G NSA X310",
    "5g-vonr": "5G VoNR simulation",
}


class PreparationError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class PreparationService:
    def __init__(self, settings: Settings, command_service: CommandService):
        self.settings = settings
        self.command_service = command_service
        self._pull_lock = threading.Lock()

    def report(self) -> PreparationReport:
        diagnostics = self.diagnostics()
        profiles = [self.profile_status(profile_id) for profile_id in PROFILE_IMAGES]
        return PreparationReport(
            checked_at=datetime.now(UTC),
            ready=all(check.status != "FAIL" for check in diagnostics) and all(profile.ready for profile in profiles),
            diagnostics=diagnostics,
            profiles=profiles,
        )

    def diagnostics(self) -> list[PreparationCheck]:
        docker = self.command_service.execute_command(
            ["docker", "info", "--format", "{{.ServerVersion}}"], dry_run=False, timeout=10
        )
        compose = self.command_service.execute_command(
            ["docker", "compose", "version", "--short"], dry_run=False, timeout=10
        )
        free_gb = shutil.disk_usage(self.settings.project_root).free / (1024 ** 3)
        tun_visible = (self.settings.project_root / "/dev/net/tun").exists()
        return [
            PreparationCheck(id="docker", label="Docker Engine", status="PASS" if docker.exit_code == 0 else "FAIL", detail=docker.stdout.strip() or "Unavailable from the backend"),
            PreparationCheck(id="compose", label="Docker Compose v2", status="PASS" if compose.exit_code == 0 else "FAIL", detail=compose.stdout.strip() or "Unavailable"),
            PreparationCheck(id="disk", label="Project disk space", status="PASS" if free_gb >= 10 else "FAIL", detail=f"{free_gb:.1f} GB free"),
            PreparationCheck(id="tun", label="TUN device", status="PASS" if tun_visible else "WARNING", detail="Visible to the backend" if tun_visible else "Not visible in the web container; startup scripts validate it"),
        ]

    def profile_status(self, profile_id: str, core_only: bool = False) -> ProfileComponentStatus:
        if profile_id == "5g-vonr-sim":
            profile_id = "5g-vonr"
        try:
            images = required_images(profile_id, core_only)
        except ValueError as exc:
            raise PreparationError(404, "IMAGE_PROFILE_NOT_FOUND", str(exc)) from exc
        statuses = [self._image_status(image) for image in images]
        installed_count = sum(image.installed for image in statuses)
        return ProfileComponentStatus(
            profile=profile_id,
            name=PROFILE_NAMES.get(profile_id, profile_id),
            rf_capable=profile_id in RF_ACCESS_IMAGES,
            core_only=core_only,
            ready=installed_count == len(statuses),
            installed_count=installed_count,
            total_count=len(statuses),
            images=statuses,
        )

    def pull(self, profile_id: str, core_only: bool = False) -> ComponentPullResponse:
        if not self.settings.image_pull_enabled:
            raise PreparationError(403, "IMAGE_PULL_DISABLED", "Image downloads are disabled by the operator.")
        if not self._pull_lock.acquire(blocking=False):
            raise PreparationError(409, "IMAGE_PULL_BUSY", "A component download is already in progress.")
        pulled: list[str] = []
        try:
            current = self.profile_status(profile_id, core_only)
            for image in current.images:
                if image.installed:
                    continue
                result = self.command_service.execute_command(
                    ["docker", "pull", image.source_image], dry_run=False, timeout=self.settings.image_pull_timeout
                )
                if result.timed_out:
                    raise PreparationError(504, "IMAGE_PULL_TIMEOUT", f"The download exceeded the allowed time: {image.source_image}")
                if result.exit_code != 0:
                    raise PreparationError(502, "IMAGE_PULL_FAILED", f"Could not download {image.source_image}.")
                if image.source_image != image.local_image:
                    tagged = self.command_service.execute_command(
                        ["docker", "tag", image.source_image, image.local_image], dry_run=False, timeout=30
                    )
                    if tagged.exit_code != 0:
                        raise PreparationError(500, "IMAGE_TAG_FAILED", f"Could not prepare {image.local_image}.")
                pulled.append(image.source_image)
            refreshed = self.profile_status(profile_id, core_only)
            return ComponentPullResponse(
                profile=refreshed,
                pulled=pulled,
                message="Components prepared without building images or starting services.",
            )
        finally:
            self._pull_lock.release()

    def ensure_ready(self, profile_id: str, core_only: bool = False) -> None:
        status = self.profile_status(profile_id, core_only)
        if not status.ready:
            raise PreparationError(409, "COMPONENTS_MISSING", "Components are missing. Prepare them before starting the scenario.")

    def _image_status(self, local_image: str) -> ComponentImageStatus:
        source, description = IMAGE_CATALOG.get(local_image, (local_image, "Official runtime image"))
        result = self.command_service.execute_command(
            ["docker", "image", "inspect", local_image], dry_run=False, timeout=10
        )
        return ComponentImageStatus(
            local_image=local_image,
            source_image=source,
            description=description,
            installed=result.exit_code == 0,
        )
