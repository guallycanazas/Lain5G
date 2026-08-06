from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from backend.app.models.subscriber import Open5GSConnectionStatus
from backend.app.services.subscriber_service import SubscriberService, SubscriberServiceError


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "subscribers"


def load_payload(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Result:
    def __init__(self, matched_count=0, deleted_count=0):
        self.matched_count = matched_count
        self.deleted_count = deleted_count


class MemoryCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction):
        self.docs.sort(key=lambda item: item.get(key, ""), reverse=direction < 0)
        return self

    def skip(self, count):
        self.docs = self.docs[count:]
        return self

    def limit(self, count):
        self.docs = self.docs[:count]
        return self

    def __iter__(self):
        return iter(deepcopy(self.docs))


class MemoryCollection:
    def __init__(self):
        self.docs = {}

    def count_documents(self, query):
        return len(self._matches(query))

    def find(self, query, projection=None):
        return MemoryCursor(self._matches(query))

    def find_one(self, query, projection=None):
        doc = self.docs.get(query.get("imsi"))
        return deepcopy(doc) if doc else None

    def insert_one(self, doc):
        self.docs[doc["imsi"]] = deepcopy(doc)

    def replace_one(self, query, doc):
        imsi = query.get("imsi")
        if imsi not in self.docs:
            return Result(matched_count=0)
        self.docs[imsi] = deepcopy(doc)
        return Result(matched_count=1)

    def delete_one(self, query):
        imsi = query.get("imsi")
        if imsi in self.docs:
            del self.docs[imsi]
            return Result(deleted_count=1)
        return Result(deleted_count=0)

    def _matches(self, query):
        if not query:
            return list(self.docs.values())
        if "$or" in query:
            prefixes = []
            for item in query["$or"]:
                for field, condition in item.items():
                    prefixes.append((field, condition["$regex"].removeprefix("^")))
            return [doc for doc in self.docs.values() if any(str(doc.get(field, "")).startswith(prefix) for field, prefix in prefixes)]
        return [doc for doc in self.docs.values() if all(doc.get(key) == value for key, value in query.items())]


class FakeConnection:
    def __init__(self, collection, status="connected"):
        self._collection = collection
        self._status = status

    def status(self):
        return Open5GSConnectionStatus(status=self._status, database="open5gs", collection="subscribers", server="mongo:27017", checked_at="2026-07-10T00:00:00Z")

    def collection(self):
        return self._collection


@pytest.fixture
def collection():
    return MemoryCollection()


@pytest.fixture
def service(real_settings, collection):
    return SubscriberService(real_settings, FakeConnection(collection))


def test_validate_valid_payload(service):
    result = service.validate_payload(load_payload("subscriber_valid.json"))

    assert result.valid is True


def test_validate_invalid_payload_does_not_expose_secret(service):
    result = service.validate_payload(load_payload("subscriber_invalid.json"))

    assert result.valid is False
    assert "not-a-key" not in " ".join(result.errors)
    assert "********" not in " ".join(result.errors)


def test_create_dry_run_does_not_persist(dry_settings, collection):
    service = SubscriberService(dry_settings, FakeConnection(collection))

    response = service.create_subscriber(load_payload("subscriber_valid.json"))

    assert response.dry_run is True
    assert response.persisted is False
    assert collection.docs == {}


def test_create_and_get_redacts_secrets(service):
    response = service.create_subscriber(load_payload("subscriber_valid.json"))

    detail = service.get_subscriber("001010000000001")

    assert response.persisted is True
    assert detail.security.k_configured is True
    assert detail.security.opc_configured is True
    assert detail.security.sqn == "************"
    assert "001122" not in detail.model_dump_json()


def test_duplicate_imsi_conflict(service):
    payload = load_payload("subscriber_valid.json")
    service.create_subscriber(payload)

    with pytest.raises(SubscriberServiceError) as exc:
        service.create_subscriber(payload)

    assert exc.value.status_code == 409


def test_list_and_search(service):
    payload = load_payload("subscriber_valid.json")
    service.create_subscriber(payload)


    listed = service.list_subscribers(search="001010")

    assert listed.total == 1
    assert listed.items[0].imsi == payload["imsi"]


def test_update_keeps_existing_secret_when_empty(service, collection):
    payload = load_payload("subscriber_valid.json")
    service.create_subscriber(payload)
    original_k = collection.docs[payload["imsi"]]["security"]["k"]

    response = service.update_subscriber(payload["imsi"], {"msisdn": "51888888888", "security": {"k": "", "opc": ""}})

    assert response.subscriber.msisdn == "51888888888"
    assert collection.docs[payload["imsi"]]["security"]["k"] == original_k


def test_update_with_new_secret(service, collection):
    payload = load_payload("subscriber_valid.json")
    service.create_subscriber(payload)

    service.update_subscriber(payload["imsi"], {"security": {"k": "11112222333344445555666677778888", "op": "88887777666655554444333322221111"}})

    security = collection.docs[payload["imsi"]]["security"]
    assert security["k"] == "11112222333344445555666677778888"
    assert security["op"] == "88887777666655554444333322221111"
    assert security["opc"] is None


def test_clone_copies_credentials_without_returning_them(service, collection):
    payload = load_payload("subscriber_valid.json")
    service.create_subscriber(payload)

    response = service.clone_subscriber(payload["imsi"], {"new_imsi": "001010000000002", "new_msisdn": "51777777777"})

    assert response.subscriber.imsi == "001010000000002"
    assert collection.docs["001010000000002"]["security"]["k"] == collection.docs[payload["imsi"]]["security"]["k"]
    assert "001122" not in response.model_dump_json()


def test_delete_requires_confirmation(service):
    payload = load_payload("subscriber_valid.json")
    service.create_subscriber(payload)

    with pytest.raises(SubscriberServiceError) as exc:
        service.delete_subscriber(payload["imsi"], confirm=False)

    assert exc.value.status_code == 400


def test_delete_and_not_found(service):
    payload = load_payload("subscriber_valid.json")
    service.create_subscriber(payload)
    service.delete_subscriber(payload["imsi"], confirm=True)

    with pytest.raises(SubscriberServiceError) as exc:
        service.get_subscriber(payload["imsi"])

    assert exc.value.status_code == 404


def test_mongodb_disconnected_returns_503(real_settings, collection):
    service = SubscriberService(real_settings, FakeConnection(collection, status="disconnected"))

    with pytest.raises(SubscriberServiceError) as exc:
        service.list_subscribers()

    assert exc.value.status_code == 503
