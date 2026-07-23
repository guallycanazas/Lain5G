from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import (
    get_deployment_service,
    get_preparation_service,
    get_profile_config_service,
    get_real_ims_service,
    get_subscriber_service,
    settings_dependency,
)
from backend.app.main import create_app
from backend.app.settings import Settings


ROOT = Path(__file__).resolve().parents[2]
RF_REQUEST = {
    "execute": True,
    "confirmation_phrase": "START 4G-LTE-X310 RF",
    "operator_note": "Authorized cabled test",
    "acknowledgements": {
        "legal_authorization_valid": True,
        "isolation_and_attenuation_verified": True,
        "channel_and_gain_reviewed": True,
        "emergency_stop_accessible": True,
    },
}
SUBSCRIBER = {
    "imsi": "001010000000001",
    "msisdn": "15551234567",
    "security": {
        "k": "00112233445566778899AABBCCDDEEFF",
        "opc": "FFEEDDCCBBAA99887766554433221100",
    },
}
REAL_IMS_SUBSCRIBER = {
    "imsi": "001010000000001",
    "msisdn": "15551234567",
    "ki": "00112233445566778899AABBCCDDEEFF",
    "opc": "FFEEDDCCBBAA99887766554433221100",
}


class BlockedService:
    def __init__(self) -> None:
        self.called = False

    def __getattr__(self, name):
        def fail_if_called(*args, **kwargs):
            self.called = True
            raise AssertionError(f"blocked service method was called: {name}")

        return fail_if_called


@pytest.mark.parametrize(
    ("method", "url", "payload", "dependency"),
    [
        ("POST", "/api/deployments/5g-sa/start", None, get_deployment_service),
        ("POST", "/api/deployments/5g-sa/stop", None, get_deployment_service),
        ("POST", "/api/deployments/5g-sa/restart", None, get_deployment_service),
        ("POST", "/api/deployments/5g-sa-x310/start-core", None, get_deployment_service),
        ("POST", "/api/deployments/5g-sa-x310/emergency-stop", None, get_deployment_service),
        ("PUT", "/api/profiles/5g-sa", {"network": {"tac": 2}}, get_profile_config_service),
        ("POST", "/api/profiles/5g-sa/apply", None, get_profile_config_service),
        ("POST", "/api/profiles/5g-sa/restore", None, get_profile_config_service),
        ("POST", "/api/preparation/profiles/5g-sa/pull", {"core_only": False}, get_preparation_service),
        ("POST", "/api/subscribers", SUBSCRIBER, get_subscriber_service),
        ("PATCH", "/api/subscribers/001010000000001", {"msisdn": "15551234568"}, get_subscriber_service),
        (
            "POST",
            "/api/subscribers/001010000000001/clone",
            {"new_imsi": "001010000000002"},
            get_subscriber_service,
        ),
        ("DELETE", "/api/subscribers/001010000000001", {"confirm": True}, get_subscriber_service),
        ("POST", "/api/ims-real/images", {"execute": True}, get_real_ims_service),
        ("POST", "/api/ims-real/start", {"mode": "4g", "execute": True}, get_real_ims_service),
        ("POST", "/api/ims-real/stop", {"mode": "4g", "execute": True}, get_real_ims_service),
        (
            "POST",
            "/api/ims-real/provision",
            {"mode": "4g", "execute": True, "subscriber": REAL_IMS_SUBSCRIBER},
            get_real_ims_service,
        ),
    ],
)
def test_mutating_routes_are_blocked_before_service_call(tmp_path, method, url, payload, dependency):
    settings = Settings(project_root=tmp_path, dry_run=False, mutating_operations_enabled=False)
    service = BlockedService()
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[dependency] = lambda: service

    with TestClient(app) as client:
        response = client.request(method, url, json=payload)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "MUTATING_OPERATIONS_DISABLED"
    assert service.called is False


def test_read_validation_and_real_ims_plan_remain_available(tmp_path):
    settings = Settings(project_root=tmp_path, dry_run=False, mutating_operations_enabled=False)

    class Profiles:
        def validate_profile(self, profile_id):
            return {"profile": profile_id, "valid": True, "errors": []}

    class RealIMS:
        def start(self, mode, mcc, mnc, *, execute=False):
            return {"mode": mode, "status": "DRY_RUN", "executed": execute}

    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_profile_config_service] = Profiles
    app.dependency_overrides[get_real_ims_service] = RealIMS

    with TestClient(app) as client:
        validation = client.post("/api/profiles/5g-sa/validate")
        plan = client.post("/api/ims-real/start", json={"mode": "4g"})

    assert validation.status_code == 200
    assert validation.json()["valid"] is True
    assert plan.status_code == 200
    assert plan.json()["executed"] is False


def test_deployment_dry_run_remains_available_when_mutations_are_disabled(tmp_path):
    settings = Settings(project_root=tmp_path, dry_run=True, mutating_operations_enabled=False)

    class Deployments:
        def start(self, scenario):
            timestamp = "2026-01-01T00:00:00Z"
            return {
                "id": scenario,
                "action": "start",
                "status": "dry_run",
                "message": "planned",
                "command": {
                    "command": ["start.sh"],
                    "cwd": ".",
                    "exit_code": 0,
                    "started_at": timestamp,
                    "finished_at": timestamp,
                    "duration_ms": 0,
                    "dry_run": True,
                },
            }

    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_deployment_service] = Deployments

    with TestClient(app) as client:
        response = client.post("/api/deployments/5g-sa/start")

    assert response.status_code == 200
    assert response.json()["command"]["dry_run"] is True


def test_rf_setting_does_not_bypass_global_mutation_gate(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        dry_run=False,
        mutating_operations_enabled=False,
        rf_web_control_enabled=True,
    )
    service = BlockedService()
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_deployment_service] = lambda: service

    with TestClient(app) as client:
        response = client.post("/api/deployments/4g-lte-x310/start-rf", json=RF_REQUEST)

    assert response.status_code == 403
    assert service.called is False


def test_global_mutation_gate_does_not_bypass_rf_authorization(deployment_service):
    deployment_service.settings.dry_run = False
    deployment_service.settings.mutating_operations_enabled = True
    deployment_service.settings.rf_web_control_enabled = False
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: deployment_service.settings
    app.dependency_overrides[get_deployment_service] = lambda: deployment_service

    with TestClient(app) as client:
        response = client.post("/api/deployments/4g-lte-x310/start-rf", json=RF_REQUEST)

    assert response.status_code == 400
    assert "RF web control is disabled" in response.json()["detail"]["message"]


def test_rf_operator_note_rejects_log_injection_before_service_call(tmp_path):
    settings = Settings(project_root=tmp_path, mutating_operations_enabled=True)
    service = BlockedService()
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_deployment_service] = lambda: service
    payload = {**RF_REQUEST, "operator_note": "approved\nINJECTED=value"}

    with TestClient(app) as client:
        response = client.post("/api/deployments/4g-lte-x310/start-rf", json=payload)

    assert response.status_code == 422
    assert "INJECTED=value" not in response.text
    assert service.called is False


def test_secure_defaults_and_compose_capability_split(tmp_path):
    settings = Settings(project_root=tmp_path, _env_file=None)
    base = (ROOT / "docker-compose.app.yml").read_text(encoding="utf-8")
    operations = (ROOT / "docker-compose.app-operations.yml").read_text(encoding="utf-8")

    assert settings.mutating_operations_enabled is False
    assert settings.image_pull_enabled is False
    assert '"127.0.0.1:${APP_BACKEND_PORT:-8000}:8000"' in base
    assert '"127.0.0.1:${APP_FRONTEND_PORT:-8080}:80"' in base
    assert "/var/run/docker.sock" not in base
    assert "read_only: true" in base
    assert "/var/run/docker.sock" in operations
