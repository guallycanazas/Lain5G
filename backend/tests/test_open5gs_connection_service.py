from __future__ import annotations

from backend.app.services.open5gs_connection_service import Open5GSConnectionService


class FakeAdmin:
    def __init__(self, error: Exception | None = None):
        self.error = error

    def command(self, name: str):
        if self.error:
            raise self.error
        return {"ok": 1}


class FakeClient:
    def __init__(self, error: Exception | None = None):
        self.admin = FakeAdmin(error)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_connection_status_dry_run(dry_settings):
    service = Open5GSConnectionService(dry_settings)

    status = service.status()

    assert status.status == "dry_run"
    assert status.database == "open5gs"


def test_connection_status_connected(real_settings, monkeypatch):
    service = Open5GSConnectionService(real_settings)
    monkeypatch.setattr(service, "_ensure_network_attachment", lambda: None)
    monkeypatch.setattr(service, "client", lambda: FakeClient())

    status = service.status()

    assert status.status == "connected"
    assert status.latency_ms is not None


def test_connection_read_does_not_attach_docker_network_without_mutation_opt_in(real_settings, monkeypatch):
    settings = real_settings.model_copy(update={"mutating_operations_enabled": False})
    service = Open5GSConnectionService(settings)
    monkeypatch.setattr(service, "client", lambda: FakeClient())

    def unexpected_docker_call(*args, **kwargs):
        raise AssertionError("read endpoint attempted a Docker network mutation")

    monkeypatch.setattr("backend.app.services.open5gs_connection_service.subprocess.run", unexpected_docker_call)

    status = service.status()

    assert status.status == "connected"


def test_connection_redacts_uri(real_settings):
    settings = real_settings.model_copy(update={"open5gs_mongo_uri": "mongodb://user:secret@mongo:27017/open5gs"})
    service = Open5GSConnectionService(settings)

    assert service.redact_uri() == "mongodb://user:***@mongo:27017/open5gs"
    assert "secret" not in service.redact_uri()


def test_connection_status_disconnected(real_settings, monkeypatch):
    from pymongo.errors import ConnectionFailure

    service = Open5GSConnectionService(real_settings)
    monkeypatch.setattr(service, "_ensure_network_attachment", lambda: None)
    monkeypatch.setattr(service, "client", lambda: FakeClient(ConnectionFailure("down")))

    status = service.status()

    assert status.status == "disconnected"


def test_connection_status_timeout(real_settings, monkeypatch):
    from pymongo.errors import ServerSelectionTimeoutError

    service = Open5GSConnectionService(real_settings)
    monkeypatch.setattr(service, "_ensure_network_attachment", lambda: None)
    monkeypatch.setattr(service, "client", lambda: FakeClient(ServerSelectionTimeoutError("timeout")))

    status = service.status()

    assert status.status == "timeout"
