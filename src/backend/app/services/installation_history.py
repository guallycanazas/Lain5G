from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models.preparation import InstallationEnvironment, InstallationRecord


INSTALLATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}\Z")


def detect_installation_environment() -> InstallationEnvironment:
    in_container = Path("/.dockerenv").exists() or bool(os.environ.get("container"))
    runtime = "Docker container" if in_container else "Host process"
    host_visible = not in_container
    host_os = platform.system() if host_visible else "Not visible from the application container"
    host_architecture = platform.machine() if host_visible else "Not visible from the application container"
    machine_type = "Not determined"
    detection_method = "Not available"

    if host_visible and platform.system() == "Linux":
        detection_method = "systemd-detect-virt"
        try:
            detected = subprocess.run(
                ["systemd-detect-virt"], capture_output=True, text=True, check=False, timeout=3
            )
            value = detected.stdout.strip()
            if detected.returncode == 0 and value and value != "none":
                machine_type = f"Virtual ({value})"
            elif detected.returncode == 1 or value == "none":
                machine_type = "Physical or hypervisor not detected"
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            detection_method = "systemd-detect-virt unavailable"

    return InstallationEnvironment(
        host_os=host_os,
        host_architecture=host_architecture,
        machine_type=machine_type,
        detection_method=detection_method,
        runtime=runtime,
        runtime_os=platform.system(),
        runtime_architecture=platform.machine(),
    )


class InstallationHistoryService:
    def __init__(self, project_root: Path):
        self.root = project_root.resolve()
        self.directory = self.root / "runs" / "installation-logs"

    def _paths(self, record_id: str) -> tuple[Path, Path]:
        if not INSTALLATION_ID_RE.fullmatch(record_id):
            raise ValueError("Invalid installation report id")
        return self.directory / f"{record_id}.json", self.directory / f"{record_id}.log"

    def write_record(self, record: InstallationRecord) -> None:
        json_path, _ = self._paths(record.id)
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = json_path.with_suffix(".json.tmp")
        temporary.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, json_path)

    def append_log(self, record_id: str, message: str) -> None:
        _, log_path = self._paths(record_id)
        self.directory.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(message)
            if not message.endswith("\n"):
                log.write("\n")

    def list_records(self, limit: int = 50) -> list[InstallationRecord]:
        if not self.directory.is_dir():
            return []
        paths = sorted(self.directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        records: list[InstallationRecord] = []
        for path in paths:
            try:
                record = InstallationRecord.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            record.log_available = path.with_suffix(".log").is_file() or path.with_suffix(".txt").is_file()
            records.append(record)
            if len(records) >= limit:
                break
        return records

    def get_record(self, record_id: str) -> InstallationRecord | None:
        json_path, log_path = self._paths(record_id)
        if not json_path.is_file():
            return None
        try:
            record = InstallationRecord.model_validate_json(json_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        record.log_available = log_path.is_file() or json_path.with_suffix(".txt").is_file()
        return record

    def log_path(self, record_id: str) -> Path | None:
        _, log_path = self._paths(record_id)
        if log_path.is_file():
            return log_path
        text_path = log_path.with_suffix(".txt")
        return text_path if text_path.is_file() else None

    @staticmethod
    def bootstrap_records(directory: Path) -> list[InstallationRecord]:
        records: list[InstallationRecord] = []
        for path in sorted(directory.glob("installation-*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            try:
                payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
                record = InstallationRecord.model_validate(payload)
            except (OSError, ValueError):
                continue
            record.log_available = path.with_suffix(".log").is_file()
            records.append(record)
        return records
