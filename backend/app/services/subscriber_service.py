from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError, ServerSelectionTimeoutError

from ..models.subscriber import (
    IMSI_RE,
    Open5GSConnectionStatus,
    SubscriberClone,
    SubscriberCreate,
    SubscriberDetail,
    SubscriberListResponse,
    SubscriberOperationResponse,
    SubscriberSecurityRedacted,
    SubscriberSummary,
    SubscriberUpdate,
    SubscriberValidationResult,
)
from ..settings import Settings
from .open5gs_connection_service import Open5GSConnectionService


class SubscriberServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class SubscriberService:
    def __init__(self, settings: Settings, connection_service: Open5GSConnectionService):
        self.settings = settings
        self.connection_service = connection_service

    def connection_status(self) -> Open5GSConnectionStatus:
        return self.connection_service.status()

    def list_subscribers(self, *, limit: int = 50, offset: int = 0, search: str | None = None) -> SubscriberListResponse:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        if self.settings.dry_run:
            return SubscriberListResponse(items=[], total=0, limit=limit, offset=offset)
        query = self._search_query(search)
        collection = self._collection_or_raise()
        try:
            total = collection.count_documents(query)
            cursor = collection.find(query, {"_id": 0}).sort("imsi", 1).skip(offset).limit(limit)
            return SubscriberListResponse(items=[self._summary(doc) for doc in cursor], total=total, limit=limit, offset=offset)
        except ServerSelectionTimeoutError as exc:
            raise SubscriberServiceError(504, "SUBSCRIBER_MONGO_TIMEOUT", "MongoDB did not respond before timeout.") from exc
        except PyMongoError as exc:
            raise SubscriberServiceError(503, "SUBSCRIBER_MONGO_UNAVAILABLE", "MongoDB is not available.") from exc

    def get_subscriber(self, imsi: str) -> SubscriberDetail:
        self._validate_imsi_path(imsi)
        if self.settings.dry_run:
            raise SubscriberServiceError(404, "SUBSCRIBER_NOT_FOUND", "Subscriber was not found.")
        doc = self._find_one_or_raise(imsi)
        return self._detail(doc)

    def validate_payload(self, payload: dict[str, Any], *, partial: bool = False) -> SubscriberValidationResult:
        try:
            SubscriberUpdate.model_validate(payload) if partial else SubscriberCreate.model_validate(payload)
        except ValidationError as exc:
            return SubscriberValidationResult(valid=False, errors=self._safe_validation_errors(exc))
        return SubscriberValidationResult(valid=True, errors=[])

    def create_subscriber(self, payload: dict[str, Any]) -> SubscriberOperationResponse:
        data = self._validate_create(payload)
        if self.settings.dry_run:
            return SubscriberOperationResponse(subscriber=self._detail(self._document_from_create(data)), dry_run=True, persisted=False, message="Dry-run: subscriber was validated but not created")
        collection = self._collection_or_raise()
        if collection.find_one({"imsi": data.imsi}, {"_id": 1}):
            raise SubscriberServiceError(409, "SUBSCRIBER_DUPLICATE_IMSI", "A subscriber with this IMSI already exists.")
        doc = self._document_from_create(data)
        try:
            collection.insert_one(doc)
        except DuplicateKeyError as exc:
            raise SubscriberServiceError(409, "SUBSCRIBER_DUPLICATE_IMSI", "A subscriber with this IMSI already exists.") from exc
        except PyMongoError as exc:
            raise SubscriberServiceError(503, "SUBSCRIBER_MONGO_UNAVAILABLE", "MongoDB is not available.") from exc
        return SubscriberOperationResponse(subscriber=self._detail(doc), message="Subscriber created. UE re-registration may be required.")

    def update_subscriber(self, imsi: str, payload: dict[str, Any]) -> SubscriberOperationResponse:
        self._validate_imsi_path(imsi)
        data = self._validate_update(payload)
        if self.settings.dry_run:
            return SubscriberOperationResponse(dry_run=True, persisted=False, message="Dry-run: subscriber update was validated but not persisted")
        collection = self._collection_or_raise()
        current = self._find_one_or_raise(imsi)
        updated = self._apply_update(current, data)
        self._validate_final_document(updated)
        updated["updatedAt"] = datetime.now(UTC)
        try:
            result = collection.replace_one({"imsi": imsi}, updated)
        except PyMongoError as exc:
            raise SubscriberServiceError(503, "SUBSCRIBER_MONGO_UNAVAILABLE", "MongoDB is not available.") from exc
        if result.matched_count != 1:
            raise SubscriberServiceError(404, "SUBSCRIBER_NOT_FOUND", "Subscriber was not found.")
        return SubscriberOperationResponse(subscriber=self._detail(updated), message="Subscriber updated. UE re-registration may be required.")

    def clone_subscriber(self, imsi: str, payload: dict[str, Any]) -> SubscriberOperationResponse:
        self._validate_imsi_path(imsi)
        try:
            clone = SubscriberClone.model_validate(payload)
        except ValidationError as exc:
            raise SubscriberServiceError(422, "SUBSCRIBER_VALIDATION_FAILED", "; ".join(self._safe_validation_errors(exc))) from exc
        if clone.new_imsi == imsi:
            raise SubscriberServiceError(409, "SUBSCRIBER_DUPLICATE_IMSI", "New IMSI must be different from the source IMSI.")
        if self.settings.dry_run:
            return SubscriberOperationResponse(dry_run=True, persisted=False, message="Dry-run: subscriber clone was validated but not persisted")
        collection = self._collection_or_raise()
        source = self._find_one_or_raise(imsi)
        if collection.find_one({"imsi": clone.new_imsi}, {"_id": 1}):
            raise SubscriberServiceError(409, "SUBSCRIBER_DUPLICATE_IMSI", "A subscriber with this IMSI already exists.")
        cloned = deepcopy(source)
        cloned.pop("_id", None)
        cloned["imsi"] = clone.new_imsi
        if clone.new_msisdn is not None:
            cloned["msisdn"] = clone.new_msisdn
        cloned["createdAt"] = datetime.now(UTC)
        cloned["updatedAt"] = datetime.now(UTC)
        try:
            collection.insert_one(cloned)
        except DuplicateKeyError as exc:
            raise SubscriberServiceError(409, "SUBSCRIBER_DUPLICATE_IMSI", "A subscriber with this IMSI already exists.") from exc
        except PyMongoError as exc:
            raise SubscriberServiceError(503, "SUBSCRIBER_MONGO_UNAVAILABLE", "MongoDB is not available.") from exc
        return SubscriberOperationResponse(subscriber=self._detail(cloned), message="Subscriber cloned. Credentials were copied internally and are not returned.")

    def delete_subscriber(self, imsi: str, *, confirm: bool) -> SubscriberOperationResponse:
        self._validate_imsi_path(imsi)
        if not confirm:
            raise SubscriberServiceError(400, "SUBSCRIBER_DELETE_CONFIRMATION_REQUIRED", "Deletion requires explicit confirmation.")
        if self.settings.dry_run:
            return SubscriberOperationResponse(dry_run=True, persisted=False, message="Dry-run: subscriber delete was validated but not persisted")
        collection = self._collection_or_raise()
        try:
            result = collection.delete_one({"imsi": imsi})
        except PyMongoError as exc:
            raise SubscriberServiceError(503, "SUBSCRIBER_MONGO_UNAVAILABLE", "MongoDB is not available.") from exc
        if result.deleted_count != 1:
            raise SubscriberServiceError(404, "SUBSCRIBER_NOT_FOUND", "Subscriber was not found.")
        return SubscriberOperationResponse(message="Subscriber deleted. Active UE sessions may persist until disconnected.")

    def _collection_or_raise(self):
        status = self.connection_service.status()
        if status.status == "connected":
            return self.connection_service.collection()
        if status.status == "timeout":
            raise SubscriberServiceError(504, "SUBSCRIBER_MONGO_TIMEOUT", "MongoDB did not respond before timeout.")
        raise SubscriberServiceError(503, "SUBSCRIBER_MONGO_UNAVAILABLE", "MongoDB is not available.")

    @staticmethod
    def _search_query(search: str | None) -> dict[str, Any]:
        if not search:
            return {}
        value = search.strip()
        if not value:
            return {}
        if not all(ch.isdigit() for ch in value):
            raise SubscriberServiceError(400, "SUBSCRIBER_INVALID_SEARCH", "Search supports IMSI or MSISDN digits only.")
        return {"$or": [{"imsi": {"$regex": f"^{value}"}}, {"msisdn": {"$regex": f"^{value}"}}]}

    @staticmethod
    def _validate_imsi_path(imsi: str) -> None:
        if not IMSI_RE.fullmatch(imsi):
            raise SubscriberServiceError(400, "SUBSCRIBER_INVALID_IMSI", "IMSI must contain 5 to 15 digits.")

    def _find_one_or_raise(self, imsi: str) -> dict[str, Any]:
        try:
            doc = self._collection_or_raise().find_one({"imsi": imsi}, {"_id": 0})
        except PyMongoError as exc:
            raise SubscriberServiceError(503, "SUBSCRIBER_MONGO_UNAVAILABLE", "MongoDB is not available.") from exc
        if not doc:
            raise SubscriberServiceError(404, "SUBSCRIBER_NOT_FOUND", "Subscriber was not found.")
        return doc

    def _validate_create(self, payload: dict[str, Any]) -> SubscriberCreate:
        try:
            return SubscriberCreate.model_validate(payload)
        except ValidationError as exc:
            raise SubscriberServiceError(422, "SUBSCRIBER_VALIDATION_FAILED", "; ".join(self._safe_validation_errors(exc))) from exc

    def _validate_update(self, payload: dict[str, Any]) -> SubscriberUpdate:
        try:
            return SubscriberUpdate.model_validate(payload)
        except ValidationError as exc:
            raise SubscriberServiceError(422, "SUBSCRIBER_VALIDATION_FAILED", "; ".join(self._safe_validation_errors(exc))) from exc

    @staticmethod
    def _safe_validation_errors(exc: ValidationError) -> list[str]:
        errors: list[str] = []
        for error in exc.errors(include_input=False):
            loc = ".".join(str(item) for item in error.get("loc", []) if item != "__root__")
            msg = str(error.get("msg", "Invalid value"))
            errors.append(f"{loc}: {msg}" if loc else msg)
        return errors or ["Invalid subscriber payload"]

    def _document_from_create(self, data: SubscriberCreate) -> dict[str, Any]:
        now = datetime.now(UTC)
        security = data.security
        doc: dict[str, Any] = {
            "imsi": data.imsi,
            "schema_version": 1,
            "subscribed_rau_tau_timer": 12,
            "network_access_mode": 0,
            "subscriber_status": 0,
            "access_restriction_data": 32,
            "security": {"k": security.k, "amf": security.amf, "op": security.op, "opc": security.opc, "sqn": security.sqn},
            "ambr": {"uplink": {"value": 1, "unit": 3}, "downlink": {"value": 1, "unit": 3}},
            "slice": [
                {
                    "sst": data.slice.sst,
                    "sd": data.slice.sd,
                    "default_indicator": True,
                    "session": [
                        {
                            "name": data.dnn,
                            "type": 3,
                            "ambr": {"uplink": {"value": 1, "unit": 3}, "downlink": {"value": 1, "unit": 3}},
                            "qos": {"index": 9, "arp": {"priority_level": 8, "pre_emption_capability": 1, "pre_emption_vulnerability": 1}},
                            "pcc_rule": [],
                        }
                    ],
                }
            ],
            "createdAt": now,
            "updatedAt": now,
        }
        if data.msisdn:
            doc["msisdn"] = data.msisdn
        return doc

    def _apply_update(self, current: dict[str, Any], data: SubscriberUpdate) -> dict[str, Any]:
        updated = deepcopy(current)
        fields = data.model_fields_set
        if "msisdn" in fields:
            if data.msisdn is None:
                updated.pop("msisdn", None)
            else:
                updated["msisdn"] = data.msisdn
        if data.security is not None:
            security = updated.setdefault("security", {})
            for key in ("k", "op", "opc", "amf", "sqn"):
                value = getattr(data.security, key)
                if value is not None:
                    security[key] = value
            if data.security.op is not None:
                security["opc"] = None
            if data.security.opc is not None:
                security["op"] = None
        if data.slice is not None:
            slice_doc = self._first_slice(updated)
            slice_doc["sst"] = data.slice.sst
            slice_doc["sd"] = data.slice.sd
        if data.dnn is not None:
            session = self._first_session(updated)
            session["name"] = data.dnn
        return updated

    def _validate_final_document(self, doc: dict[str, Any]) -> None:
        security = doc.get("security") or {}
        if not security.get("k") or not (security.get("op") or security.get("opc")):
            raise SubscriberServiceError(422, "SUBSCRIBER_VALIDATION_FAILED", "Final subscriber document must keep K and OP or OPc.")
        if security.get("op") and security.get("opc"):
            raise SubscriberServiceError(422, "SUBSCRIBER_VALIDATION_FAILED", "Final subscriber document cannot contain both OP and OPc.")

    def _summary(self, doc: dict[str, Any]) -> SubscriberSummary:
        security = doc.get("security") or {}
        slice_doc = self._first_slice(doc, create=False)
        session = self._first_session(doc, create=False)
        return SubscriberSummary(
            imsi=str(doc.get("imsi", "")),
            msisdn=doc.get("msisdn"),
            dnn=session.get("name") if session else None,
            sst=slice_doc.get("sst") if slice_doc else None,
            sd=slice_doc.get("sd") if slice_doc else None,
            security=SubscriberSecurityRedacted(
                k_configured=bool(security.get("k")),
                op_configured=bool(security.get("op")),
                opc_configured=bool(security.get("opc")),
                amf=security.get("amf"),
                sqn="************" if security.get("sqn") else None,
            ),
        )

    def _detail(self, doc: dict[str, Any]) -> SubscriberDetail:
        return SubscriberDetail(**self._summary(doc).model_dump(), checked_at=datetime.now(UTC))

    @staticmethod
    def _first_slice(doc: dict[str, Any], *, create: bool = True) -> dict[str, Any]:
        slices = doc.setdefault("slice", []) if create else doc.get("slice", [])
        if slices:
            return slices[0]
        if not create:
            return {}
        slices.append({"session": []})
        return slices[0]

    def _first_session(self, doc: dict[str, Any], *, create: bool = True) -> dict[str, Any]:
        slice_doc = self._first_slice(doc, create=create)
        sessions = slice_doc.setdefault("session", []) if create else slice_doc.get("session", [])
        if sessions:
            return sessions[0]
        if not create:
            return {}
        sessions.append({})
        return sessions[0]
