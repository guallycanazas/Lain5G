from __future__ import annotations

from datetime import UTC, datetime

from ..models.run import RunDetail
from ..models.validation import ValidationCheck, ValidationReport, ValidationState
from .run_service import RunService


class ValidationService:
    def __init__(self, run_service: RunService):
        self.run_service = run_service

    def latest_validation(self, *, scenario: str | None = None) -> ValidationReport | None:
        run = self.run_service.latest_run(scenario=scenario)
        if not run:
            return None
        return self.report_from_run(run)

    def report_from_run(self, run: RunDetail) -> ValidationReport:
        scenario = str(run.metadata.get("scenario") or "unknown")
        checks = self._checks_from_payload(run.validation or {})
        status = self._overall_status(checks)
        return ValidationReport(
            run_id=run.run_id,
            scenario=scenario,
            status=status,
            validation={check.id: check.status for check in checks},
            checks=checks,
            checked_at=self._parse_checked_at(run.validation or {}),
        )

    def dry_run_report(self, scenario: str) -> ValidationReport:
        checks = [
            ValidationCheck(id=name, status="NOT_TESTED", detail="dry-run mode")
            for name in [
                "mongo",
                "nrf",
                "amf",
                "smf",
                "upf",
                "ausf",
                "udm",
                "udr",
                "pcf",
                "ng_connection",
                "ue_registration",
                "pdu_session",
                "ue_tun",
                "ue_ip",
                "ping",
            ]
        ]
        return ValidationReport(
            run_id=None,
            scenario=scenario,
            status="NOT_TESTED",
            validation={check.id: check.status for check in checks},
            checks=checks,
            checked_at=datetime.now(UTC),
        )

    def _checks_from_payload(self, payload: dict) -> list[ValidationCheck]:
        raw_checks = payload.get("checks")
        if not isinstance(raw_checks, list):
            return []
        checks: list[ValidationCheck] = []
        for raw in raw_checks:
            if not isinstance(raw, dict):
                continue
            check_id = raw.get("id")
            status = raw.get("status")
            if not isinstance(check_id, str) or status not in {"PASS", "FAIL", "WARNING", "NOT_TESTED"}:
                continue
            checks.append(ValidationCheck(id=check_id, status=status, detail=raw.get("detail")))
        return checks

    @staticmethod
    def _overall_status(checks: list[ValidationCheck]) -> ValidationState:
        if not checks:
            return "NOT_TESTED"
        statuses = [check.status for check in checks]
        if "FAIL" in statuses:
            return "FAIL"
        if "WARNING" in statuses:
            return "WARNING"
        if all(status == "PASS" for status in statuses):
            return "PASS"
        return "NOT_TESTED"

    @staticmethod
    def _parse_checked_at(payload: dict) -> datetime | None:
        value = payload.get("checked_at")
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
