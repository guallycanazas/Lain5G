from __future__ import annotations

import json
import socket
import subprocess
from datetime import UTC, datetime
from time import perf_counter
from urllib.parse import urlsplit, urlunsplit

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, OperationFailure, PyMongoError, ServerSelectionTimeoutError

from ..models.subscriber import Open5GSConnectionStatus
from ..settings import Settings


class Open5GSConnectionService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def status(self) -> Open5GSConnectionStatus:
        if self.settings.dry_run:
            return self._status("dry_run", self._server_label())
        try:
            self._ensure_network_attachment()
            started = perf_counter()
            with self.client() as client:
                client.admin.command("ping")
            latency_ms = int((perf_counter() - started) * 1000)
            return self._status("connected", self._server_label(), latency_ms=latency_ms)
        except ServerSelectionTimeoutError:
            return self._status("timeout", self._server_label(), message="MongoDB did not respond before timeout")
        except ConfigurationError:
            return self._status("misconfigured", self._server_label(), message="MongoDB configuration is invalid")
        except OperationFailure:
            return self._status("error", self._server_label(), message="MongoDB rejected the operation")
        except (ConnectionFailure, OSError, PyMongoError):
            return self._status("disconnected", self._server_label(), message="MongoDB is not available")

    def client(self) -> MongoClient:
        timeout_ms = self.settings.subscriber_operation_timeout * 1000
        return MongoClient(
            self.settings.open5gs_mongo_uri,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            socketTimeoutMS=timeout_ms,
            uuidRepresentation="standard",
        )

    def collection(self):
        client = self.client()
        return client[self.settings.open5gs_mongo_database][self.settings.open5gs_subscriber_collection]

    def redact_uri(self) -> str:
        try:
            parts = urlsplit(self.settings.open5gs_mongo_uri)
        except ValueError:
            return "[invalid-uri]"
        netloc = parts.netloc
        if "@" in netloc:
            userinfo, host = netloc.rsplit("@", 1)
            user = userinfo.split(":", 1)[0]
            netloc = f"{user}:***@{host}"
        return urlunsplit((parts.scheme, netloc, parts.path, "", ""))

    def _status(self, status: str, server: str, *, latency_ms: int | None = None, message: str | None = None) -> Open5GSConnectionStatus:
        return Open5GSConnectionStatus(
            status=status,  # type: ignore[arg-type]
            database=self.settings.open5gs_mongo_database,
            collection=self.settings.open5gs_subscriber_collection,
            server=server,
            latency_ms=latency_ms,
            checked_at=datetime.now(UTC),
            message=message,
        )

    def _server_label(self) -> str:
        try:
            parts = urlsplit(self.settings.open5gs_mongo_uri)
        except ValueError:
            return "[invalid-uri]"
        return parts.netloc.rsplit("@", 1)[-1] or "[unknown]"

    def _ensure_network_attachment(self) -> None:
        if not self.settings.mutating_operations_enabled:
            return
        network = self.settings.open5gs_docker_network.strip()
        if not network:
            return
        if not self._mongo_container_running():
            return
        hostname = socket.gethostname()
        try:
            inspect = subprocess.run(
                ["docker", "network", "inspect", network, "--format", "{{json .Containers}}"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
                shell=False,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return
        if inspect.returncode != 0:
            return
        try:
            containers = json.loads(inspect.stdout or "{}")
        except json.JSONDecodeError:
            return
        for data in containers.values():
            if data.get("Name") == hostname or data.get("Name") == "lain5g-lab-app-backend":
                return
        subprocess.run(["docker", "network", "connect", network, hostname], capture_output=True, text=True, timeout=5, check=False, shell=False)

    @staticmethod
    def _mongo_container_running() -> bool:
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", "lain5g-lab-5g-sa-mongo"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
                shell=False,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return False
        return result.returncode == 0 and result.stdout.strip() == "true"
