from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..models.real_ims import PyHSSProvisioningReport, RealIMSSubscriber, ResourceResult


RequestTransport = Callable[[str, str, dict[str, Any] | None, dict[str, Any] | None], Any]


class PyHSSError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PyHSSService:
    """Reconcile pyHSS resources through an operator-supplied request transport."""

    def __init__(self, request_transport: RequestTransport) -> None:
        self._transport = request_transport

    def health(self) -> dict[str, Any]:
        payload = self._request("GET", "/swagger.json")
        if not isinstance(payload, dict):
            raise PyHSSError("pyHSS health endpoint returned an invalid document")
        return payload

    def provision(self, subscriber: RealIMSSubscriber, mcc: str, mnc: str) -> PyHSSProvisioningReport:
        domain = ims_domain(mcc, mnc)
        results: list[ResourceResult] = []

        internet_id, action = self._reconcile_apn(subscriber.apn_internet, qci=9)
        results.append(ResourceResult(resource=f"apn:{subscriber.apn_internet}", resource_id=internet_id, action=action))
        ims_id, action = self._reconcile_apn(subscriber.apn_ims, qci=5)
        results.append(ResourceResult(resource=f"apn:{subscriber.apn_ims}", resource_id=ims_id, action=action))

        auc_payload = {
            "imsi": subscriber.imsi,
            "ki": subscriber.ki,
            "opc": subscriber.opc,
            "amf": subscriber.amf,
            "sqn": subscriber.sqn,
            "esim": False,
        }
        auc, action = self._reconcile_identity("auc", f"/auc/imsi/{subscriber.imsi}", "auc_id", auc_payload)
        auc_id = _required_id(auc, "auc_id")
        results.append(ResourceResult(resource="auc", resource_id=auc_id, action=action))

        packet_payload = {
            "imsi": subscriber.imsi,
            "enabled": subscriber.enabled,
            "auc_id": auc_id,
            "default_apn": internet_id,
            "apn_list": f"{internet_id},{ims_id}",
            "msisdn": subscriber.msisdn,
            "ue_ambr_dl": 999999,
            "ue_ambr_ul": 999999,
            "nam": 0,
            "roaming_enabled": True,
            "subscribed_rau_tau_timer": 300,
        }
        packet, action = self._reconcile_identity(
            "subscriber", f"/subscriber/imsi/{subscriber.imsi}", "subscriber_id", packet_payload
        )
        packet_id = _required_id(packet, "subscriber_id")
        results.append(ResourceResult(resource="subscriber", resource_id=packet_id, action=action))

        scscf_host = f"scscf.{domain}"
        ims_payload = {
            "imsi": subscriber.imsi,
            "msisdn": subscriber.msisdn,
            "msisdn_list": f"[{subscriber.msisdn}]",
            "ifc_path": "default_ifc.xml",
            "sh_template_path": "default_sh_user_data.xml",
            "scscf": f"sip:{scscf_host}:6060",
            "scscf_realm": domain,
            "scscf_peer": scscf_host,
        }
        ims, action = self._reconcile_identity(
            "ims_subscriber",
            f"/ims_subscriber/ims_subscriber_imsi/{subscriber.imsi}",
            "ims_subscriber_id",
            ims_payload,
        )
        ims_id = _required_id(ims, "ims_subscriber_id")
        results.append(ResourceResult(resource="ims_subscriber", resource_id=ims_id, action=action))
        return PyHSSProvisioningReport(status="PASS", imsi=subscriber.imsi, resources=results)

    def verify_subscriber(self, imsi: str) -> list[ResourceResult]:
        resources = (
            ("auc", f"/auc/imsi/{imsi}", "auc_id"),
            ("subscriber", f"/subscriber/imsi/{imsi}", "subscriber_id"),
            ("ims_subscriber", f"/ims_subscriber/ims_subscriber_imsi/{imsi}", "ims_subscriber_id"),
        )
        return [
            ResourceResult(resource=name, resource_id=_required_id(self._request("GET", path), field), action="verified")
            for name, path, field in resources
        ]

    def list_packet_subscribers(self) -> list[dict[str, Any]]:
        return self._list("/subscriber/list")

    def list_ims_subscribers(self) -> list[dict[str, Any]]:
        return self._list("/ims_subscriber/list")

    def _list(self, path: str) -> list[dict[str, Any]]:
        payload = self._request("GET", path, query={"page": 0, "page_size": 1000})
        if not isinstance(payload, list):
            raise PyHSSError(f"pyHSS {path} returned an invalid list")
        return [item for item in payload if isinstance(item, dict)]

    def _reconcile_apn(self, name: str, qci: int) -> tuple[int, str]:
        desired = {
            "apn": name,
            "ip_version": 0,
            "charging_characteristics": "0800",
            "apn_ambr_dl": 999999,
            "apn_ambr_ul": 999999,
            "qci": qci,
            "arp_priority": 4,
            "arp_preemption_capability": False,
            "arp_preemption_vulnerability": True,
            "nbiot": False,
        }
        listed = self._request("GET", "/apn/list", query={"page": 0, "page_size": 200})
        existing = next(
            (item for item in listed if isinstance(item, dict) and item.get("apn") == name),
            None,
        ) if isinstance(listed, list) else None
        if existing is None:
            created = self._request("PUT", "/apn/", desired)
            return _required_id(created, "apn_id"), "created"
        resource_id = _required_id(existing, "apn_id")
        if _matches(existing, desired):
            return resource_id, "verified"
        updated = self._request("PATCH", f"/apn/{resource_id}", desired)
        return _required_id(updated, "apn_id"), "updated"

    def _reconcile_identity(
        self,
        resource: str,
        lookup_path: str,
        id_field: str,
        desired: dict[str, Any],
    ) -> tuple[dict[str, Any], str]:
        try:
            existing = self._request("GET", lookup_path)
        except PyHSSError as exc:
            if exc.status_code not in {400, 404}:
                raise
            existing = None
        if isinstance(existing, dict) and existing.get(id_field) is not None:
            if _matches(existing, desired):
                return existing, "verified"
            resource_id = _required_id(existing, id_field)
            updated = self._request("PATCH", f"/{resource}/{resource_id}", desired)
            if not isinstance(updated, dict):
                raise PyHSSError(f"pyHSS returned invalid {resource} update data")
            return updated, "updated"
        created = self._request("PUT", f"/{resource}/", desired)
        if not isinstance(created, dict):
            raise PyHSSError(f"pyHSS returned invalid {resource} creation data")
        return created, "created"

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        try:
            return self._transport(method, path, body, query)
        except PyHSSError as exc:
            raise PyHSSError(f"pyHSS {method} {path} request failed", exc.status_code) from exc
        except Exception as exc:
            # Transport exceptions are deliberately not interpolated: they can contain the body.
            raise PyHSSError(f"pyHSS {method} {path} request failed") from exc


def _matches(existing: dict[str, Any], desired: dict[str, Any]) -> bool:
    return all(existing.get(key) == value for key, value in desired.items())


def _required_id(payload: Any, field: str) -> int:
    if not isinstance(payload, dict) or payload.get(field) is None:
        raise PyHSSError(f"pyHSS response is missing {field}")
    try:
        return int(payload[field])
    except (TypeError, ValueError) as exc:
        raise PyHSSError(f"pyHSS response contains an invalid {field}") from exc


def ims_domain(mcc: str, mnc: str) -> str:
    if not re_fullmatch_digits(mcc, 3) or not (re_fullmatch_digits(mnc, 2) or re_fullmatch_digits(mnc, 3)):
        raise ValueError("MCC must contain 3 digits and MNC 2 or 3 digits")
    return f"ims.mnc{mnc.zfill(3)}.mcc{mcc}.3gppnetwork.org"


def re_fullmatch_digits(value: str, length: int) -> bool:
    return len(value) == length and value.isascii() and value.isdigit()
