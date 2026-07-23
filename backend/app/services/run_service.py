from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models.run import RunDetail, RunSummary
from ..settings import Settings


RUN_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class RunSecurityError(ValueError):
    pass


class RunService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.project_root = settings.project_root.resolve()
        self.runs_dir = (self.project_root / "runs").resolve()

    def list_runs(self, *, limit: int | None = None, scenario: str | None = None, status: str | None = None) -> list[RunSummary]:
        if not self.runs_dir.exists():
            return []
        summaries: list[RunSummary] = []
        for child in self.runs_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                self._ensure_inside_runs(child.resolve())
                metadata = self._read_json(child / "metadata.json", required=True)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if not isinstance(metadata, dict) or not metadata.get("run_id"):
                continue
            validation = self._read_optional_json(child / "validation.json")
            validation_status = self._validation_status(validation if isinstance(validation, dict) else None)
            if scenario and metadata.get("scenario") != scenario:
                continue
            summary_status = validation_status or metadata.get("status")
            if status and summary_status != status:
                continue
            summaries.append(self._summary_from_metadata(metadata, status=summary_status))

        summaries.sort(key=self._summary_sort_key, reverse=True)
        if limit is not None:
            return summaries[:limit]
        return summaries

    def get_run(self, run_id: str) -> RunDetail | None:
        run_dir = self._run_dir(run_id)
        if not run_dir.is_dir():
            return None
        metadata = self._read_json(run_dir / "metadata.json", required=True)
        if not isinstance(metadata, dict):
            return None
        validation = self._read_optional_json(run_dir / "validation.json")
        metrics = self._read_optional_json(run_dir / "metrics.json")
        return RunDetail(
            run_id=str(metadata.get("run_id", run_id)),
            metadata=metadata,
            validation=validation if isinstance(validation, dict) else None,
            metrics=metrics if isinstance(metrics, dict) else None,
            logs=self._list_logs(run_dir),
            loaded_at=datetime.now(UTC),
        )

    def latest_run(self, *, scenario: str | None = None) -> RunDetail | None:
        summaries = self.list_runs(limit=1, scenario=scenario)
        if not summaries:
            return None
        return self.get_run(summaries[0].run_id)

    def _summary_from_metadata(self, metadata: dict[str, Any], *, status: str | None = None) -> RunSummary:
        return RunSummary(
            run_id=str(metadata.get("run_id", "")),
            scenario=metadata.get("scenario"),
            deployment_path=metadata.get("deployment_path"),
            started_at=metadata.get("started_at"),
            finished_at=metadata.get("finished_at"),
            status=status or metadata.get("status"),
            git_commit=metadata.get("git_commit"),
            validated_claims=metadata.get("validated_claims") if isinstance(metadata.get("validated_claims"), list) else [],
        )

    @staticmethod
    def _validation_status(validation: dict[str, Any] | None) -> str | None:
        if not validation:
            return None
        status = validation.get("status")
        if isinstance(status, str) and status:
            return status
        checks = validation.get("checks")
        if not isinstance(checks, list) or not checks:
            return None
        statuses = [check.get("status") for check in checks if isinstance(check, dict)]
        if "FAIL" in statuses:
            return "FAIL"
        if "WARNING" in statuses:
            return "WARNING"
        if statuses and all(item == "PASS" for item in statuses):
            return "PASS"
        return "NOT_TESTED"

    @staticmethod
    def _summary_sort_key(summary: RunSummary) -> str:
        return summary.started_at or summary.run_id

    def _run_dir(self, run_id: str) -> Path:
        if not RUN_ID_RE.fullmatch(run_id) or run_id in {".", ".."}:
            raise RunSecurityError("Invalid run id")
        run_dir = (self.runs_dir / run_id).resolve()
        self._ensure_inside_runs(run_dir)
        return run_dir

    def _ensure_inside_runs(self, path: Path) -> None:
        if path != self.runs_dir and self.runs_dir not in path.parents:
            raise RunSecurityError("Path is outside runs directory")

    def _read_json(self, path: Path, *, required: bool) -> dict[str, Any] | None:
        resolved = path.resolve()
        self._ensure_inside_runs(resolved)
        if not resolved.exists():
            if required:
                raise FileNotFoundError(str(path))
            return None
        if not resolved.is_file():
            if required:
                raise ValueError("Expected a file")
            return None
        with resolved.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else None

    def _read_optional_json(self, path: Path) -> dict[str, Any] | None:
        try:
            return self._read_json(path, required=False)
        except (OSError, ValueError, json.JSONDecodeError):
            return None

    def _list_logs(self, run_dir: Path) -> list[str]:
        logs_dir = (run_dir / "logs").resolve()
        self._ensure_inside_runs(logs_dir)
        if not logs_dir.is_dir():
            return []
        logs: list[str] = []
        for item in logs_dir.iterdir():
            try:
                resolved = item.resolve()
                self._ensure_inside_runs(resolved)
            except (OSError, ValueError):
                continue
            if resolved.is_file():
                logs.append(item.name)
        return sorted(logs)
