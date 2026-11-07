import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..models.sim_programmer import SimProgramRequest
from ..settings import Settings


class SimProgrammerError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class SimProgrammerService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def status(self) -> dict:
        if not self.settings.sim_programmer_token:
            return {"available": False, "programming_enabled": self.settings.mutating_operations_enabled, "readers": [], "message": "SIM programming bridge is not configured."}
        try:
            result = self._request("GET", "/readers")
            return {"available": True, "programming_enabled": self.settings.mutating_operations_enabled, "readers": result.get("readers", []), "message": "PC/SC bridge is ready."}
        except SimProgrammerError:
            return {"available": False, "programming_enabled": self.settings.mutating_operations_enabled, "readers": [], "message": "PC/SC bridge is offline. Restart OpenLain5G in operations mode and check the connected reader."}

    def inspect(self, reader_index: int) -> dict:
        if not self.settings.sim_programmer_token:
            raise SimProgrammerError(503, "SIM_PROGRAMMER_UNAVAILABLE", "SIM programming bridge is not configured.")
        try:
            return self._request("POST", "/inspect", {"reader_index": reader_index})
        except SimProgrammerError as exc:
            raise exc

    def program(self, payload: SimProgramRequest) -> dict:
        if not self.settings.mutating_operations_enabled:
            raise SimProgrammerError(403, "MUTATING_OPERATIONS_DISABLED", "Enable local mutating operations before programming a SIM.")
        if not self.settings.sim_programmer_token:
            raise SimProgrammerError(503, "SIM_PROGRAMMER_UNAVAILABLE", "SIM programming bridge is not configured.")
        body = payload.model_dump()
        # The bridge receives credentials only for this request and never returns or logs them.
        try:
            return self._request("POST", "/program", body, timeout=45)
        except SimProgrammerError as exc:
            raise exc

    def _request(self, method: str, path: str, body: dict | None = None, timeout: int = 5) -> dict:
        request = Request(
            f"{self.settings.sim_programmer_url.rstrip('/')}{path}",
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers={"Authorization": f"Bearer {self.settings.sim_programmer_token}", "Content-Type": "application/json"},
            method=method,
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read(16384))
        except HTTPError as exc:
            try:
                result = json.loads(exc.read(4096))
            except Exception:
                result = {}
            raise SimProgrammerError(exc.code, result.get("code", "SIM_PROGRAMMER_ERROR"), result.get("message", "The SIM programming bridge rejected the request.")) from None
        except (URLError, TimeoutError, OSError, json.JSONDecodeError):
            raise SimProgrammerError(503, "SIM_PROGRAMMER_UNAVAILABLE", "The SIM programming bridge is offline or did not respond.") from None
        if not isinstance(result, dict):
            raise SimProgrammerError(502, "SIM_PROGRAMMER_BAD_RESPONSE", "The SIM programming bridge returned an invalid response.")
        return result
