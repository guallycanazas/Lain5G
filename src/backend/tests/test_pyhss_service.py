from copy import deepcopy

from backend.app.models.real_ims import RealIMSSubscriber
from backend.app.services.pyhss_service import PyHSSError, PyHSSService


class MemoryTransport:
    def __init__(self):
        self.apns = []
        self.resources = {"auc": {}, "subscriber": {}, "ims_subscriber": {}}
        self.next_ids = {"apn": 1, "auc": 10, "subscriber": 20, "ims_subscriber": 30}
        self.calls = []

    def __call__(self, method, path, body, query):
        self.calls.append((method, path, deepcopy(body), deepcopy(query)))
        if method == "GET" and path == "/apn/list":
            return list(self.apns)
        if path.startswith("/apn/"):
            return self._write_apn(method, path, body)
        resource = path.strip("/").split("/")[0]
        if method == "GET":
            imsi = path.rsplit("/", 1)[-1]
            return self.resources[resource].get(imsi)
        if method == "PUT":
            resource_id = self.next_ids[resource]
            item = {**body, f"{resource}_id": resource_id}
            self.resources[resource][body["imsi"]] = item
            return item
        resource_id = int(path.rsplit("/", 1)[-1])
        item = {**body, f"{resource}_id": resource_id}
        self.resources[resource][body["imsi"]] = item
        return item

    def _write_apn(self, method, path, body):
        if method == "PUT":
            item = {**body, "apn_id": self.next_ids["apn"]}
            self.next_ids["apn"] += 1
            self.apns.append(item)
            return item
        apn_id = int(path.rsplit("/", 1)[-1])
        item = {**body, "apn_id": apn_id}
        self.apns = [item if existing["apn_id"] == apn_id else existing for existing in self.apns]
        return item


def subscriber():
    return RealIMSSubscriber(
        imsi="001010000000001",
        msisdn="15551234567",
        ki="00112233445566778899AABBCCDDEEFF",
        opc="FFEEDDCCBBAA99887766554433221100",
    )


def test_pyhss_reconciliation_is_idempotent_and_transport_is_injected():
    transport = MemoryTransport()
    service = PyHSSService(transport)

    first = service.provision(subscriber(), "001", "01")
    second = service.provision(subscriber(), "001", "01")

    assert [item.action for item in first.resources] == ["created"] * 5
    assert [item.action for item in second.resources] == ["verified"] * 5
    assert len(transport.apns) == 2
    assert all(len(items) == 1 for items in transport.resources.values())
    serialized = second.model_dump_json()
    assert subscriber().ki not in serialized
    assert subscriber().opc not in serialized


def test_transport_exception_does_not_echo_request_secrets():
    def failing_transport(method, path, body, query):
        raise RuntimeError(str(body))

    service = PyHSSService(failing_transport)
    secret = subscriber()
    try:
        service.provision(secret, "001", "01")
    except Exception as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected transport failure")

    assert secret.ki not in message
    assert secret.opc not in message


def test_transport_pyhss_error_is_also_sanitized():
    secret = subscriber()

    def failing_transport(method, path, body, query):
        raise PyHSSError(secret.ki, 404)

    service = PyHSSService(failing_transport)
    try:
        service.provision(secret, "001", "01")
    except Exception as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected transport failure")

    assert secret.ki not in message
