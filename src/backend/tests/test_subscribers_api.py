from __future__ import annotations

import json
from pathlib import Path

from backend.app.dependencies import get_subscriber_service
from backend.app.models.subscriber import Open5GSConnectionStatus
from backend.app.services.subscriber_service import SubscriberService

from .test_subscriber_service import FakeConnection, MemoryCollection


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "subscribers"


def load_payload(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def override_subscribers(client, settings):
    collection = MemoryCollection()
    service = SubscriberService(settings, FakeConnection(collection))
    client.app.dependency_overrides[get_subscriber_service] = lambda: service
    return service


def test_connection_endpoint(client, real_settings):
    service = override_subscribers(client, real_settings)

    response = client.get("/api/subscribers/connection")

    assert response.status_code == 200
    assert response.json()["status"] == "connected"


def test_crud_endpoints_do_not_expose_secrets(client, real_settings):
    override_subscribers(client, real_settings)
    payload = load_payload("subscriber_valid.json")

    created = client.post("/api/subscribers", json=payload)
    assert created.status_code == 201
    assert "001122" not in created.text

    listed = client.get("/api/subscribers")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert "001122" not in listed.text

    detail = client.get(f"/api/subscribers/{payload['imsi']}")
    assert detail.status_code == 200
    assert detail.json()["security"]["sqn"] == "************"

    updated = client.patch(f"/api/subscribers/{payload['imsi']}", json={"msisdn": "51888888888"})
    assert updated.status_code == 200
    assert updated.json()["subscriber"]["msisdn"] == "51888888888"

    cloned = client.post(f"/api/subscribers/{payload['imsi']}/clone", json={"new_imsi": "001010000000002"})
    assert cloned.status_code == 201
    assert cloned.json()["subscriber"]["imsi"] == "001010000000002"

    deleted = client.request("DELETE", "/api/subscribers/001010000000002", json={"confirm": True})
    assert deleted.status_code == 200


def test_validate_endpoint_sanitizes_errors(client, real_settings):
    override_subscribers(client, real_settings)

    response = client.post("/api/subscribers/validate", json=load_payload("subscriber_invalid.json"))

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert "not-a-key" not in response.text


def test_duplicate_returns_409(client, real_settings):
    override_subscribers(client, real_settings)
    payload = load_payload("subscriber_valid.json")
    assert client.post("/api/subscribers", json=payload).status_code == 201

    response = client.post("/api/subscribers", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SUBSCRIBER_DUPLICATE_IMSI"


def test_delete_requires_confirmation(client, real_settings):
    override_subscribers(client, real_settings)

    response = client.request("DELETE", "/api/subscribers/001010000000001", json={"confirm": False})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "SUBSCRIBER_DELETE_CONFIRMATION_REQUIRED"
