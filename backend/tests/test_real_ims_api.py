from fastapi.testclient import TestClient

from backend.app.dependencies import get_real_ims_service, settings_dependency
from backend.app.main import create_app
from backend.app.services.real_ims_service import RealIMSError
from backend.app.settings import Settings


class FakeRealIMSService:
    def __init__(self):
        self.calls = []
        self.fail = False

    def build_images(self, *, execute=False, force=False):
        self.calls.append(("images", execute, force))
        return {"executed": execute, "status": "PASS" if execute else "DRY_RUN"}

    def start(self, mode, mcc, mnc, *, execute=False):
        self.calls.append(("start", mode, mcc, mnc, execute))
        if self.fail:
            raise RealIMSError("00112233445566778899AABBCCDDEEFF")
        return {"mode": mode, "executed": execute, "status": "PASS" if execute else "DRY_RUN"}

    def stop(self, mode, *, execute=False):
        self.calls.append(("stop", mode, execute))
        return {"mode": mode, "executed": execute, "status": "PASS" if execute else "DRY_RUN"}

    def provision(self, mode, subscriber, mcc, mnc, *, execute=False):
        self.calls.append(("provision", mode, subscriber.imsi, execute))
        return {"mode": mode, "imsi": subscriber.imsi, "executed": execute, "status": "DRY_RUN"}

    def subscribers(self, mode):
        self.calls.append(("subscribers", mode))
        return {"mode": mode, "count": 0, "subscribers": [], "secrets_redacted": True}


def client_for(service, *, mutations_enabled=False):
    app = create_app()
    app.dependency_overrides[get_real_ims_service] = lambda: service
    app.dependency_overrides[settings_dependency] = lambda: Settings(mutating_operations_enabled=mutations_enabled)
    return TestClient(app)


def test_mutating_routes_are_dry_run_by_default():
    service = FakeRealIMSService()
    with client_for(service) as client:
        assert client.post("/api/ims-real/images").json()["executed"] is False
        assert client.post("/api/ims-real/start", json={"mode": "4g"}).json()["executed"] is False
        assert client.post("/api/ims-real/stop", json={"mode": "4g"}).json()["executed"] is False
        response = client.post(
            "/api/ims-real/provision",
            json={
                "mode": "4g",
                "subscriber": {
                    "imsi": "001010000000001",
                    "msisdn": "15551234567",
                    "ki": "00112233445566778899AABBCCDDEEFF",
                    "opc": "FFEEDDCCBBAA99887766554433221100",
                },
            },
        )
        assert response.status_code == 200
        assert response.json()["executed"] is False
    assert all(call[-1] is False for call in service.calls)


def test_validation_response_redacts_subscriber_keys():
    ki = "00112233445566778899AABBCCDDEEFF"
    opc = "FFEEDDCCBBAA99887766554433221100"
    with client_for(FakeRealIMSService()) as client:
        response = client.post(
            "/api/ims-real/provision",
            json={
                "mode": "4g",
                "mcc": "999",
                "mnc": "99",
                "subscriber": {"imsi": "001010000000001", "msisdn": "15551234567", "ki": ki, "opc": opc},
            },
        )

    assert response.status_code == 422
    assert ki not in response.text
    assert opc not in response.text


def test_field_validation_response_redacts_invalid_key_input():
    invalid_key = "SECRET-KEY-MATERIAL"
    with client_for(FakeRealIMSService()) as client:
        response = client.post(
            "/api/ims-real/provision",
            json={
                "mode": "4g",
                "subscriber": {
                    "imsi": "001010000000001",
                    "msisdn": "15551234567",
                    "ki": invalid_key,
                    "opc": "FFEEDDCCBBAA99887766554433221100",
                },
            },
        )

    assert response.status_code == 422
    assert invalid_key not in response.text


def test_service_errors_are_controlled_and_redacted():
    service = FakeRealIMSService()
    service.fail = True
    with client_for(service, mutations_enabled=True) as client:
        response = client.post("/api/ims-real/start", json={"mode": "4g", "execute": True})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "REAL_IMS_CONFLICT"
    assert "00112233445566778899AABBCCDDEEFF" not in response.text


def test_subscriber_list_is_explicitly_redacted():
    with client_for(FakeRealIMSService()) as client:
        response = client.get("/api/ims-real/subscribers?mode=4g")

    assert response.status_code == 200
    assert response.json() == {"mode": "4g", "count": 0, "subscribers": [], "secrets_redacted": True}
