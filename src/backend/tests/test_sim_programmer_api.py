from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.dependencies import get_sim_programmer_service, settings_dependency
from backend.app.main import create_app
from backend.app.settings import Settings


VALID_PROGRAM = {
    "reader_index": 0,
    "mcc": "001",
    "mnc": "01",
    "imsi": "001011234567895",
    "iccid": "8901234567890123455",
    "ki": "00112233445566778899aabbccddeeff",
    "opc": "ffeeddccbbaa99887766554433221100",
    "adm": "12345678",
    "confirm": True,
}


class FakeSimProgrammer:
    def __init__(self, *, programming_enabled: bool = True) -> None:
        self.program_payload = None
        self.programming_enabled = programming_enabled

    def status(self):
        return {
            "available": True,
            "programming_enabled": self.programming_enabled,
            "readers": ["Test PC/SC reader"],
            "message": "PC/SC bridge is ready.",
        }

    def inspect(self, reader_index: int):
        assert reader_index == 0
        return {
            "reader": "Test PC/SC reader",
            "detected": True,
            "recognized": True,
            "supported": True,
            "card": "sysmoUSIM-SJS1",
            "message": "Supported test USIM detected.",
        }

    def program(self, payload):
        self.program_payload = payload
        return {
            "success": True,
            "reader": "Test PC/SC reader",
            "card": "sysmoUSIM-SJS1",
            "imsi": payload.imsi,
            "iccid": payload.iccid,
            "verified_fields": ["ICCID", "Ki", "OPc", "IMSI", "MNC length"],
            "message": "SIM programming and read-back verification completed.",
        }


def test_status_and_card_inspection_are_available_without_mutations(tmp_path):
    settings = Settings(project_root=tmp_path, mutating_operations_enabled=False)
    service = FakeSimProgrammer(programming_enabled=False)
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_sim_programmer_service] = lambda: service

    with TestClient(app) as client:
        status = client.get("/api/sim-programmer/status")
        inspected = client.post("/api/sim-programmer/inspect", json={"reader_index": 0})

    assert status.status_code == 200
    assert status.json()["readers"] == ["Test PC/SC reader"]
    assert status.json()["programming_enabled"] is False
    assert inspected.status_code == 200
    assert inspected.json()["supported"] is True
    assert "Ki" not in inspected.text
    app.dependency_overrides.clear()


def test_program_requires_explicit_mutation_enablement(tmp_path):
    settings = Settings(project_root=tmp_path, mutating_operations_enabled=False)
    service = FakeSimProgrammer()
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_sim_programmer_service] = lambda: service

    with TestClient(app) as client:
        response = client.post("/api/sim-programmer/program", json=VALID_PROGRAM)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "MUTATING_OPERATIONS_DISABLED"
    assert service.program_payload is None
    app.dependency_overrides.clear()


def test_program_returns_verified_card_identity_without_authentication_keys(tmp_path):
    settings = Settings(project_root=tmp_path, mutating_operations_enabled=True)
    service = FakeSimProgrammer()
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_sim_programmer_service] = lambda: service

    with TestClient(app) as client:
        response = client.post("/api/sim-programmer/program", json=VALID_PROGRAM)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["verified_fields"] == ["ICCID", "Ki", "OPc", "IMSI", "MNC length"]
    assert response.json()["imsi"] == VALID_PROGRAM["imsi"]
    assert VALID_PROGRAM["ki"] not in response.text
    assert VALID_PROGRAM["opc"] not in response.text
    assert "76543210" not in response.text
    assert service.program_payload is not None
    assert service.program_payload.ki == VALID_PROGRAM["ki"]
    app.dependency_overrides.clear()


def test_invalid_sim_credentials_are_redacted_from_validation_response(tmp_path):
    settings = Settings(project_root=tmp_path, mutating_operations_enabled=True)
    service = FakeSimProgrammer()
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_sim_programmer_service] = lambda: service
    payload = {**VALID_PROGRAM, "ki": "private-invalid-sim-key"}

    with TestClient(app) as client:
        response = client.post("/api/sim-programmer/program", json=payload)

    assert response.status_code == 422
    assert "private-invalid-sim-key" not in response.text
    assert service.program_payload is None
    app.dependency_overrides.clear()
