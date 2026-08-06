from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from backend.app.settings import Settings
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


def test_reserved_backend_ip_cannot_overlap_static_core_addresses():
    with pytest.raises(ValueError, match="must remain 10.20.0.250"):
        Settings(LAIN5G_OPEN5GS_DOCKER_IP="10.20.0.3")


def test_network_attachment_uses_reserved_backend_ip(real_settings, monkeypatch):
    service = Open5GSConnectionService(real_settings)
    calls: list[list[str]] = []
    attached = False
    monkeypatch.setattr("backend.app.services.open5gs_connection_service.socket.gethostname", lambda: "backend-container-id")

    def run(command, **kwargs):
        nonlocal attached
        calls.append(command)
        if command[1:3] == ["network", "inspect"]:
            containers = {"backend": {"Name": "lain5g-lab-app-backend", "IPv4Address": "10.20.0.250/24"}} if attached else {}
            return SimpleNamespace(returncode=0, stdout=json.dumps(containers))
        if command[1:3] == ["network", "connect"]:
            attached = True
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr("backend.app.services.open5gs_connection_service.subprocess.run", run)

    service._ensure_network_attachment()

    assert [
        "docker", "network", "connect", "--ip", "10.20.0.250",
        "lain5g-lab-5g-sa-core", "backend-container-id",
    ] in calls


def test_network_attachment_moves_backend_off_static_core_ip(real_settings, monkeypatch):
    service = Open5GSConnectionService(real_settings)
    calls: list[list[str]] = []
    monkeypatch.setattr("backend.app.services.open5gs_connection_service.socket.gethostname", lambda: "backend-container-id")
    current_ip: str | None = "10.20.0.3"

    def run(command, **kwargs):
        nonlocal current_ip
        calls.append(command)
        if command[1:3] == ["network", "inspect"]:
            containers = {"backend": {"Name": "lain5g-lab-app-backend", "IPv4Address": f"{current_ip}/24"}} if current_ip else {}
            return SimpleNamespace(returncode=0, stdout=json.dumps(containers))
        if command[1:3] == ["network", "disconnect"]:
            current_ip = None
        if command[1:3] == ["network", "connect"]:
            current_ip = "10.20.0.250"
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr("backend.app.services.open5gs_connection_service.subprocess.run", run)

    service._ensure_network_attachment()

    assert [
        "docker", "network", "disconnect", "lain5g-lab-5g-sa-core", "backend-container-id",
    ] in calls
    assert [
        "docker", "network", "connect", "--ip", "10.20.0.250",
        "lain5g-lab-5g-sa-core", "backend-container-id",
    ] in calls


def test_network_attachment_rejects_failed_migration(real_settings, monkeypatch):
    service = Open5GSConnectionService(real_settings)
    monkeypatch.setattr("backend.app.services.open5gs_connection_service.socket.gethostname", lambda: "backend-container-id")
    containers = {"backend": {"Name": "lain5g-lab-app-backend", "IPv4Address": "10.20.0.3/24"}}

    def run(command, **kwargs):
        if command[1:3] == ["network", "inspect"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(containers))
        return SimpleNamespace(returncode=1, stdout="")

    monkeypatch.setattr("backend.app.services.open5gs_connection_service.subprocess.run", run)

    with pytest.raises(OSError, match="Could not disconnect"):
        service._ensure_network_attachment()

    monkeypatch.setattr(
        "backend.app.services.open5gs_connection_service.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("docker", 3)),
    )
    with pytest.raises(OSError, match="Could not inspect"):
        service._ensure_network_attachment()
