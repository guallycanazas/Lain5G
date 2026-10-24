from __future__ import annotations

import shutil
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ..models.preparation import ComponentImageStatus, ComponentPullImageProgress, ComponentPullJob, ComponentPullResponse, DockerHostInfo, PreparationCheck, PreparationReport, ProfileComponentStatus
from ..settings import Settings
from .command_service import DOCKER_HOST_INFO_FORMAT, CommandService
from .image_catalog import IMAGE_CATALOG, PROFILE_IMAGES, PUBLIC_PROFILE_IDS, RF_ACCESS_IMAGES, required_images
from .scenario_environment import prepare_scenario_environment


PROFILE_NAMES = {
    "4g-lte-sim": "4G LTE simulation",
    "4g-volte-sim": "4G VoLTE simulation",
    "4g-lte-x310": "4G LTE X310",
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
        self._jobs_lock = threading.Lock()
        self._jobs: dict[str, ComponentPullJob] = {}
        self._active_job_id: str | None = None

    def report(self) -> PreparationReport:
        diagnostics = self.diagnostics()
        profiles = [self.profile_status(profile_id) for profile_id in PUBLIC_PROFILE_IDS]
        return PreparationReport(
            checked_at=datetime.now(UTC),
            ready=all(check.status != "FAIL" for check in diagnostics) and all(profile.ready for profile in profiles),
            diagnostics=diagnostics,
            profiles=profiles,
            docker_host=self.docker_host_info(),
        )

    def docker_host_info(self) -> DockerHostInfo | None:
        result = self.command_service.execute_command(
            ["docker", "info", "--format", DOCKER_HOST_INFO_FORMAT],
            dry_run=False,
            timeout=10,
            preserve_stdout=True,
        )
        if result.exit_code != 0:
            return None
        values = result.stdout.split("|")
        if len(values) != 19:
            return None
        disk = shutil.disk_usage(self.settings.project_root)
        dmi = self._dmi_host_info()
        return DockerHostInfo(
            name=values[0] or None,
            operating_system=values[1] or None,
            os_version=values[2] or None,
            os_type=values[3] or None,
            architecture=values[4] or None,
            manufacturer=dmi["manufacturer"],
            product_name=dmi["product_name"],
            firmware_vendor=dmi["firmware_vendor"],
            firmware_version=dmi["firmware_version"],
            board_name=dmi["board_name"],
            virtualization=dmi["virtualization"],
            cpu_model=self._cpu_model(),
            physical_cores=self._physical_core_count(),
            kernel_version=values[5] or None,
            docker_version=values[6] or None,
            storage_driver=values[7] or None,
            docker_root_dir=values[8] or None,
            cgroup_driver=values[9] or None,
            cgroup_version=values[10] or None,
            cpus=self._optional_int(values[11]),
            memory_bytes=self._optional_int(values[12]),
            containers_total=self._optional_int(values[14]),
            containers_running=self._optional_int(values[15]),
            containers_paused=self._optional_int(values[16]),
            containers_stopped=self._optional_int(values[17]),
            images_count=self._optional_int(values[18]),
            workspace_disk_total_bytes=disk.total,
            workspace_disk_free_bytes=disk.free,
        )

    @staticmethod
    def _optional_int(value: str) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _cpu_model() -> str | None:
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
                for line in cpuinfo:
                    key, separator, value = line.partition(":")
                    if separator and key.strip().lower() in {"model name", "hardware"} and value.strip():
                        return value.strip()
        except OSError:
            pass
        return None

    @staticmethod
    def _dmi_host_info() -> dict[str, str | None]:
        dmi_root = Path("/sys/class/dmi/id")
        fields = {
            "manufacturer": "sys_vendor",
            "product_name": "product_name",
            "firmware_vendor": "bios_vendor",
            "firmware_version": "bios_version",
            "board_name": "board_name",
        }
        values: dict[str, str | None] = {}
        for output_key, filename in fields.items():
            try:
                value = (dmi_root / filename).read_text(encoding="utf-8").strip()
                values[output_key] = value or None
            except OSError:
                values[output_key] = None

        vendor = values["manufacturer"] or ""
        product = values["product_name"] or ""
        dmi_signature = f"{vendor} {product}".lower()
        virtual_signatures = {
            "qemu": "QEMU/KVM",
            "kvm": "KVM",
            "vmware": "VMware",
            "virtualbox": "VirtualBox",
            "innotek": "VirtualBox",
            "microsoft corporation virtual machine": "Microsoft Hyper-V",
            "xen": "Xen",
            "amazon ec2": "Amazon EC2 VM",
            "google": "Google Cloud VM",
            "openstack": "OpenStack VM",
            "parallels": "Parallels",
            "bhyve": "bhyve",
            "bochs": "Bochs",
            "libvirt": "libvirt VM",
        }
        virtualization = next((label for signature, label in virtual_signatures.items() if signature in dmi_signature), None)
        if virtualization is None:
            try:
                cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore").lower()
                if any(line.startswith("flags") and " hypervisor " in f" {line} " for line in cpuinfo.splitlines()):
                    virtualization = "Virtual machine (hypervisor flag)"
            except OSError:
                pass
        physical_vendor_signatures = (
            "asustek", "asus", "dell inc.", "hewlett-packard", "hp", "lenovo", "gigabyte", "micro-star",
            "msi", "acer", "apple inc.", "framework", "system76", "purism",
        )
        if virtualization is None and product and any(signature in vendor.lower() for signature in physical_vendor_signatures):
            virtualization = "Native hardware (DMI)"
        values["virtualization"] = virtualization or "Unknown"
        return values

    @staticmethod
    def _physical_core_count() -> int | None:
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None
        cores = set()
        for processor in cpuinfo.split("\n\n"):
            fields = {key.strip(): value.strip() for line in processor.splitlines() if ":" in line for key, value in [line.split(":", 1)]}
            physical_id = fields.get("physical id", "0")
            core_id = fields.get("core id", "")
            if core_id:
                cores.add((physical_id, core_id))
        return len(cores) or None

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

    def start_pull(self, profile_id: str, core_only: bool = False) -> ComponentPullJob:
        if not self.settings.image_pull_enabled:
            raise PreparationError(403, "IMAGE_PULL_DISABLED", "Image downloads are disabled by the operator.")
        current = self.profile_status(profile_id, core_only)
        missing = [image for image in current.images if not image.installed]
        with self._jobs_lock:
            if len(self._jobs) >= 100:
                completed = sorted(
                    (job for job in self._jobs.values() if job.state in {"succeeded", "failed"}),
                    key=lambda job: job.finished_at or job.created_at,
                )
                for expired in completed[: len(self._jobs) - 99]:
                    del self._jobs[expired.job_id]
            active = self._jobs.get(self._active_job_id or "")
            if active and active.state in {"queued", "running"}:
                raise PreparationError(409, "IMAGE_PULL_BUSY", f"Component download {active.job_id} is already in progress.")
            job = ComponentPullJob(
                job_id=f"pull-{uuid4().hex}",
                scope=profile_id,
                core_only=core_only,
                state="queued" if missing else "succeeded",
                images=[
                    ComponentPullImageProgress(
                        local_image=image.local_image,
                        source_image=image.source_image,
                        description=image.description,
                    )
                    for image in missing
                ],
                total_count=len(missing),
                overall_percent=0 if missing else 100,
                created_at=datetime.now(UTC),
                finished_at=None if missing else datetime.now(UTC),
            )
            self._jobs[job.job_id] = job
            if not missing:
                return job.model_copy(deep=True)
            if not self._pull_lock.acquire(blocking=False):
                del self._jobs[job.job_id]
                raise PreparationError(409, "IMAGE_PULL_BUSY", "A component download is already in progress.")
            self._active_job_id = job.job_id
        worker = threading.Thread(target=self._run_pull_job, args=(job.job_id,), daemon=True, name=f"lain5g-{job.job_id}")
        worker.start()
        with self._jobs_lock:
            return self._jobs[job.job_id].model_copy(deep=True)

    def pull_job(self, job_id: str) -> ComponentPullJob:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise PreparationError(404, "IMAGE_PULL_NOT_FOUND", "Component download was not found.")
            return job.model_copy(deep=True)

    def active_pull(self) -> ComponentPullJob | None:
        with self._jobs_lock:
            job = self._jobs.get(self._active_job_id or "")
            return job.model_copy(deep=True) if job and job.state in {"queued", "running"} else None

    def _run_pull_job(self, job_id: str) -> None:
        try:
            with self._jobs_lock:
                job = self._jobs[job_id]
                job.state = "running"
                job.started_at = datetime.now(UTC)
            for index in range(self._jobs[job_id].total_count):
                with self._jobs_lock:
                    job = self._jobs[job_id]
                    image = job.images[index]
                    image.state = "pulling"
                    job.current_image = image.local_image
                    job.current_index = index + 1
                    source_image = image.source_image
                    local_image = image.local_image
                result = self.command_service.execute_command(
                    ["docker", "pull", source_image], dry_run=False, timeout=self.settings.image_pull_timeout
                )
                if result.timed_out:
                    self._fail_pull_job(job_id, index, "IMAGE_PULL_TIMEOUT", f"The download exceeded the allowed time: {source_image}")
                    return
                if result.exit_code != 0:
                    self._fail_pull_job(job_id, index, "IMAGE_PULL_FAILED", f"Could not download {source_image}.")
                    return
                if source_image != local_image:
                    with self._jobs_lock:
                        self._jobs[job_id].images[index].state = "tagging"
                    tagged = self.command_service.execute_command(
                        ["docker", "tag", source_image, local_image], dry_run=False, timeout=30
                    )
                    if tagged.exit_code != 0:
                        self._fail_pull_job(job_id, index, "IMAGE_TAG_FAILED", f"Could not prepare {local_image}.")
                        return
                with self._jobs_lock:
                    job = self._jobs[job_id]
                    job.images[index].state = "succeeded"
                    job.pulled.append(source_image)
                    job.completed_count = index + 1
                    job.overall_percent = round(job.completed_count * 100 / job.total_count)
            with self._jobs_lock:
                job = self._jobs[job_id]
                job.state = "succeeded"
                job.current_image = None
                job.finished_at = datetime.now(UTC)
                job.overall_percent = 100
        except Exception:
            self._fail_pull_job(job_id, None, "IMAGE_PULL_FAILED", "The component download ended unexpectedly.")
        finally:
            with self._jobs_lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None
            self._pull_lock.release()

    def _fail_pull_job(self, job_id: str, image_index: int | None, code: str, message: str) -> None:
        with self._jobs_lock:
            job = self._jobs[job_id]
            job.state = "failed"
            job.error_code = code
            job.error_message = message
            job.finished_at = datetime.now(UTC)
            if image_index is not None:
                image = job.images[image_index]
                image.state = "failed"
                image.error_code = code
                image.error_message = message

    def ensure_ready(self, profile_id: str, core_only: bool = False) -> None:
        status = self.profile_status(profile_id, core_only)
        if not status.ready:
            raise PreparationError(409, "COMPONENTS_MISSING", "Components are missing. Prepare them before starting the scenario.")

    def prepare_environment(self, profile_id: str) -> Path:
        try:
            target, _ = prepare_scenario_environment(self.settings.project_root, profile_id)
        except ValueError as exc:
            raise PreparationError(404, "ENVIRONMENT_PROFILE_NOT_FOUND", str(exc)) from exc
        except (OSError, UnicodeError) as exc:
            raise PreparationError(500, "ENVIRONMENT_PREPARATION_FAILED", "Could not prepare the private scenario environment.") from exc
        return target

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
