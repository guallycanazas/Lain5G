from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from ..models.real_ims import (
    Mode,
    PLMN,
    RealIMSCheck,
    RealIMSStatusReport,
    RealIMSSubscriber,
    RealIMSSubscriberList,
    RealIMSSubscriberSummary,
)
from ..settings import Settings
from ..version import VERSION
from .pyhss_service import PyHSSError, PyHSSService


PYHSS_IMAGE = f"lain5g-lab/pyhss-secure:{VERSION}"
FIRST_PARTY_IMAGES = {
    f"lain5g-lab/ims-real-open5gs:{VERSION}": "ims-real-open5gs",
    f"lain5g-lab/ims-real-kamailio:{VERSION}": "ims-real-kamailio",
    PYHSS_IMAGE: "pyhss-secure",
    f"lain5g-lab/ims-real-mysql:{VERSION}": "ims-real-mysql",
    f"lain5g-lab/ims-real-dns:{VERSION}": "ims-real-dns",
    f"lain5g-lab/ims-real-rtpengine:{VERSION}": "ims-real-rtpengine",
}
ALLOWED_DOCKER_SUBCOMMANDS = {"build", "compose", "image"}
ALLOWED_COMPOSE_ACTIONS = {"down", "exec", "logs", "ps", "up", "version", "ls"}
COMPOSE_OPTIONS_WITH_VALUE = {"-f", "--env-file", "-p", "--project-name"}
COMPOSE_PATH_OPTIONS = {"-f", "--env-file"}

PYHSS_REQUEST_HELPER = r"""import json,sys
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
e=json.load(sys.stdin)
url='http://127.0.0.1:8080'+e['path']
if e.get('query'): url+='?'+urlencode(e['query'])
body=json.dumps(e['body']).encode() if e.get('body') is not None else None
h={'Accept':'application/json'}
if body is not None: h['Content-Type']='application/json'
if e.get('key'): h['Provisioning-Key']=e['key']
try:
 r=urlopen(Request(url,data=body,headers=h,method=e['method']),timeout=10)
 raw=r.read().decode()
 print(raw if raw else 'null')
except HTTPError as x:
 print(json.dumps({'_error':'http','status':x.code}))
except (URLError,OSError):
 print(json.dumps({'_error':'unreachable'}))
"""


class RealIMSError(RuntimeError):
    pass


class RealIMSService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.project_root = settings.project_root.resolve()
        self.stack_dir = self._confined(self.project_root / "deployments" / "ims-real")
        self.images_dir = self._confined(self.project_root / "images")

    def preflight(self, mode: Mode) -> RealIMSStatusReport:
        self._validate_mode(mode)
        manifest = self._manifest(mode)
        required_files = [
            manifest,
            self.stack_dir / "env.defaults",
            self.stack_dir / "config-provenance.json",
            self.stack_dir / "images.lock.yaml",
            self.images_dir / "pyhss-secure" / "runtime" / "config.yaml",
            self.images_dir / "pyhss-secure" / "runtime" / "default_ifc.xml",
            self.images_dir / "pyhss-secure" / "runtime" / "default_sh_user_data.xml",
            self.images_dir / "pyhss-secure" / "runtime" / "pyhss_init.sh",
        ]
        missing_files = [str(path) for path in required_files if not path.is_file()]
        checks = [
            RealIMSCheck(
                id="stack_files",
                status="PASS" if not missing_files else "FAIL",
                message="Real IMS stack files are present" if not missing_files else "Required real IMS stack files are missing",
                evidence={"missing": missing_files},
            )
        ]
        unpublished = self._pyhss_is_unpublished(manifest) if manifest.is_file() else False
        checks.append(
            RealIMSCheck(
                id="pyhss_not_published",
                status="PASS" if unpublished else "FAIL",
                message="pyHSS has no host port publication" if unpublished else "pyHSS must not publish host ports",
            )
        )
        docker = self._run(["docker", "compose", "version"], check=False)
        docker_ok = docker.returncode == 0
        checks.append(self._check("docker", docker_ok, "Docker Compose is available" if docker_ok else "Docker Compose is unavailable"))

        missing_contexts = [
            str(self.images_dir / context)
            for context in FIRST_PARTY_IMAGES.values()
            if not (self.images_dir / context / "Dockerfile").is_file()
        ]
        checks.append(
            RealIMSCheck(
                id="image_contexts",
                status="PASS" if not missing_contexts else "FAIL",
                message="All first-party image contexts are present" if not missing_contexts else "First-party image contexts are missing",
                evidence={"missing": missing_contexts},
            )
        )
        missing_images = [] if docker_ok else sorted(FIRST_PARTY_IMAGES)
        if docker_ok:
            for image in FIRST_PARTY_IMAGES:
                if self._run(["docker", "image", "inspect", image], check=False).returncode != 0:
                    missing_images.append(image)
        checks.append(
            RealIMSCheck(
                id="first_party_images",
                status="PASS" if not missing_images else "FAIL",
                message="All first-party real IMS images are present" if not missing_images else "First-party images must be built explicitly",
                evidence={"required": sorted(FIRST_PARTY_IMAGES), "missing": sorted(missing_images)},
            )
        )
        return self._report(mode, checks)

    def build_images(self, *, execute: bool = False, force: bool = False) -> dict[str, Any]:
        planned = [
            ["docker", "build", "-t", image, str(self.images_dir / context)]
            for image, context in FIRST_PARTY_IMAGES.items()
        ]
        if not execute:
            return {"status": "DRY_RUN", "executed": False, "force": force, "commands": planned}
        built: list[str] = []
        reused: list[str] = []
        for image, context_name in FIRST_PARTY_IMAGES.items():
            context = self.images_dir / context_name
            if not (context / "Dockerfile").is_file():
                raise RealIMSError(f"missing image build context: images/{context_name}")
            present = self._run(["docker", "image", "inspect", image], check=False).returncode == 0
            if present and not force:
                reused.append(image)
                continue
            self._run(["docker", "build", "-t", image, str(context)], timeout=600)
            built.append(image)
        return {"status": "PASS", "executed": True, "built": built, "reused": reused}

    def start(self, mode: Mode, mcc: str = "001", mnc: str = "01", *, execute: bool = False) -> dict[str, Any]:
        self._validate_mode(mode)
        PLMN(mcc=mcc, mnc=mnc)
        env_file = self._state_dir(mode) / "stack.env"
        command = self._compose_command(mode, env_file, "up") + ["-d", *self._services(mode)]
        if not execute:
            return {
                "mode": mode,
                "status": "DRY_RUN",
                "executed": False,
                "mcc": mcc,
                "mnc": mnc,
                "command": command,
                "rf_started": False,
            }
        self._enforce_mutual_exclusion(mode)
        report = self.preflight(mode)
        failures = [check.message for check in report.checks if check.status == "FAIL"]
        if failures:
            raise RealIMSError("real IMS preflight failed: " + "; ".join(failures))
        env_file = self._prepare_runtime(mode, mcc=mcc, mnc=mnc)
        command = self._compose_command(mode, env_file, "up") + ["-d", *self._services(mode)]
        self._run(command, timeout=300)
        return {
            "mode": mode,
            "status": "RUNNING",
            "executed": True,
            "mcc": mcc,
            "mnc": mnc,
            "services": self._services(mode),
            "rf_started": False,
        }

    def stop(self, mode: Mode, *, execute: bool = False) -> dict[str, Any]:
        self._validate_mode(mode)
        env_file = self._state_dir(mode) / "stack.env"
        command = self._compose_command(mode, env_file, "down")
        if not execute:
            return {"mode": mode, "status": "DRY_RUN", "executed": False, "command": command, "volumes_deleted": False}
        if not env_file.is_file():
            env_file = self._prepare_runtime(mode)
        completed = self._run(self._compose_command(mode, env_file, "down"), check=False, timeout=180)
        return {
            "mode": mode,
            "status": "STOPPED" if completed.returncode == 0 else "WARNING",
            "executed": True,
            "returncode": completed.returncode,
            "volumes_deleted": False,
        }

    def provision(
        self,
        mode: Mode,
        subscriber: RealIMSSubscriber,
        mcc: str = "001",
        mnc: str = "01",
        *,
        execute: bool = False,
    ) -> dict[str, Any]:
        self._validate_mode(mode)
        PLMN(mcc=mcc, mnc=mnc)
        if not subscriber.imsi.startswith(f"{mcc}{mnc}"):
            raise RealIMSError("subscriber IMSI does not match the requested MCC/MNC")
        if not execute:
            return {
                "mode": mode,
                "status": "DRY_RUN",
                "executed": False,
                "imsi": subscriber.imsi,
                "resources": ["open5gs", "pyhss:apn", "pyhss:auc", "pyhss:subscriber", "pyhss:ims_subscriber"],
            }
        env_file = self._require_matching_runtime(mode, mcc, mnc)
        open5gs = self._provision_open5gs(mode, env_file, subscriber)
        pyhss = self._pyhss(mode, env_file).provision(subscriber, mcc, mnc)
        report = {
            "mode": mode,
            "status": "PASS",
            "executed": True,
            "imsi": subscriber.imsi,
            "open5gs": open5gs,
            "pyhss": pyhss.model_dump(mode="json"),
        }
        self._write_json(self._state_dir(mode) / "provisioning.json", report)
        return report

    def status(self, mode: Mode, imsi: str | None = None) -> RealIMSStatusReport:
        self._validate_mode(mode)
        if imsi is not None and not re.fullmatch(r"[0-9]{14,15}", imsi):
            raise RealIMSError("IMSI must contain 14 or 15 digits")
        env_file = self._state_dir(mode) / "stack.env"
        if not env_file.is_file():
            return self._report(mode, [self._check("runtime", False, "Real IMS mode has not been initialized")])
        completed = self._run(self._compose_command(mode, env_file, "ps") + ["--format", "json"], check=False)
        running = _running_services(completed.stdout)
        required = set(self._services(mode))
        missing = sorted(required - running)
        checks: list[RealIMSCheck] = [
            RealIMSCheck(
                id="services",
                status="PASS" if not missing else "FAIL",
                message="All required real IMS services are running" if not missing else "Required real IMS services are not running",
                evidence={"running": sorted(running), "missing": missing},
            )
        ]
        try:
            self._pyhss(mode, env_file).health()
            checks.append(self._check("pyhss_api", True, "pyHSS API is reachable inside the Compose project"))
        except PyHSSError:
            checks.append(self._check("pyhss_api", False, "pyHSS API is not ready inside the Compose project"))
        checks.extend(self._listener_checks(mode, env_file))
        checks.append(self._cx_check(mode, env_file))
        checks.append(self._policy_check(mode, env_file, running))
        if imsi:
            checks.extend(self._subscriber_checks(mode, env_file, imsi))
        checks.append(self._registration_check(mode, env_file))
        return self._report(mode, checks)

    def subscribers(self, mode: Mode) -> RealIMSSubscriberList:
        self._validate_mode(mode)
        env_file = self._state_dir(mode) / "stack.env"
        if not env_file.is_file():
            raise RealIMSError("real IMS mode must be started before listing subscribers")

        pyhss = self._pyhss(mode, env_file)
        ims_records = pyhss.list_ims_subscribers()
        packet_records = {
            str(item.get("imsi")): item
            for item in pyhss.list_packet_subscribers()
            if item.get("imsi") is not None
        }
        open5gs_records = self._open5gs_subscribers(mode, env_file)
        open5gs_by_imsi = {
            str(item.get("imsi")): item
            for item in open5gs_records
            if item.get("imsi") is not None
        }

        summaries: list[RealIMSSubscriberSummary] = []
        for record in ims_records:
            imsi = str(record.get("imsi") or "")
            if not re.fullmatch(r"[0-9]{14,15}", imsi):
                continue
            packet = packet_records.get(imsi, {})
            open5gs = open5gs_by_imsi.get(imsi)
            msisdn = str(record.get("msisdn") or packet.get("msisdn") or "")
            domain = str(record.get("scscf_realm") or "")
            summaries.append(
                RealIMSSubscriberSummary(
                    imsi=imsi,
                    msisdn=msisdn,
                    impi=f"{imsi}@{domain}" if domain else imsi,
                    impu=f"sip:{msisdn}@{domain}" if msisdn and domain else "",
                    domain=domain,
                    scscf=str(record.get("scscf")) if record.get("scscf") else None,
                    enabled=bool(packet.get("enabled", True)),
                    apns=_open5gs_apns(open5gs),
                    open5gs_present=open5gs is not None,
                    pyhss_present=True,
                )
            )
        summaries.sort(key=lambda item: item.imsi)
        return RealIMSSubscriberList(mode=mode, count=len(summaries), subscribers=summaries)

    def _open5gs_subscribers(self, mode: Mode, env_file: Path) -> list[dict[str, Any]]:
        script = (
            "print(JSON.stringify(db.getSiblingDB('open5gs').subscribers.find({}, "
            "{imsi:1, msisdn:1, subscriber_status:1, slice:1, _id:0}).toArray()));"
        )
        command = self._compose_command(mode, env_file, "exec") + ["-T", "mongo", "mongosh", "--quiet", "open5gs", "--eval", script]
        result = self._run(command)
        return _last_json_array(result.stdout)

    def _provision_open5gs(self, mode: Mode, env_file: Path, subscriber: RealIMSSubscriber) -> dict[str, Any]:
        encoded = json.dumps(_open5gs_document(subscriber), separators=(",", ":"))
        script = (
            f"const subscriber = JSON.parse({json.dumps(encoded)});\n"
            "const database = db.getSiblingDB('open5gs');\n"
            "const result = database.subscribers.updateOne({imsi: subscriber.imsi}, {$set: subscriber}, {upsert: true});\n"
            "print(JSON.stringify({acknowledged: result.acknowledged, matched: result.matchedCount, modified: result.modifiedCount, upserted: result.upsertedCount || (result.upsertedId ? 1 : 0)}));\n"
        )
        command = self._compose_command(mode, env_file, "exec") + ["-T", "mongo", "mongosh", "--quiet", "open5gs"]
        completed = self._run(command, input_text=script)
        result = _last_json_object(completed.stdout)
        if not result.get("acknowledged"):
            raise RealIMSError("Open5GS did not acknowledge subscriber reconciliation")
        return {
            "status": "PASS",
            "imsi": subscriber.imsi,
            "matched": int(result.get("matched", 0)),
            "modified": int(result.get("modified", 0)),
            "created": bool(result.get("upserted", 0)) or int(result.get("matched", 0)) == 0,
        }

    def _subscriber_checks(self, mode: Mode, env_file: Path, imsi: str) -> list[RealIMSCheck]:
        script = f"print(db.getSiblingDB('open5gs').subscribers.countDocuments({{imsi: {json.dumps(imsi)}}}));\n"
        command = self._compose_command(mode, env_file, "exec") + ["-T", "mongo", "mongosh", "--quiet", "open5gs"]
        result = self._run(command, input_text=script, check=False)
        count = _last_integer(result.stdout)
        checks = [self._check("open5gs_subscriber", count == 1, f"Open5GS subscriber record count: {count}")]
        try:
            resources = self._pyhss(mode, env_file).verify_subscriber(imsi)
            checks.append(
                RealIMSCheck(
                    id="pyhss_subscriber",
                    status="PASS",
                    message="AuC, packet and IMS subscriber records are synchronized",
                    evidence={"resources": [item.model_dump(mode="json") for item in resources]},
                )
            )
        except PyHSSError:
            checks.append(self._check("pyhss_subscriber", False, "pyHSS subscriber records are not synchronized"))
        return checks

    def _listener_checks(self, mode: Mode, env_file: Path) -> list[RealIMSCheck]:
        checks: list[RealIMSCheck] = []
        for service, port in (("pcscf", 5060), ("icscf", 4060), ("scscf", 6060)):
            result = self._run(self._compose_command(mode, env_file, "exec") + ["-T", service, "ss", "-lntu"], check=False)
            listening = result.returncode == 0 and re.search(rf":{port}\b", result.stdout) is not None
            checks.append(self._check(f"{service}_sip_listener", listening, f"{service} SIP listener on port {port}" if listening else f"{service} SIP listener is not ready"))
        return checks

    def _cx_check(self, mode: Mode, env_file: Path) -> RealIMSCheck:
        connected: list[str] = []
        for service in ("icscf", "scscf"):
            result = self._run(self._compose_command(mode, env_file, "exec") + ["-T", service, "ss", "-ntp"], check=False)
            if result.returncode == 0 and "ESTAB" in result.stdout and re.search(r":3875\b", result.stdout):
                connected.append(service)
        ready = connected == ["icscf", "scscf"]
        return RealIMSCheck(
            id="diameter_cx",
            status="PASS" if ready else "WARNING",
            message="I-CSCF and S-CSCF Cx peers are established" if ready else "Cx peer establishment is incomplete",
            evidence={"connected": connected},
        )

    def _policy_check(self, mode: Mode, env_file: Path, running: set[str]) -> RealIMSCheck:
        if mode == "4g":
            result = self._run(self._compose_command(mode, env_file, "exec") + ["-T", "pcscf", "ss", "-ntp"], check=False)
            ready = result.returncode == 0 and "ESTAB" in result.stdout and re.search(r":3873\b", result.stdout) is not None
            return RealIMSCheck(
                id="ims_policy_path",
                status="PASS" if ready else "WARNING",
                message="P-CSCF Diameter Rx is established" if ready else "P-CSCF Diameter Rx is not established",
                evidence={"mode": "Rx"},
            )
        result = self._run(self._compose_command(mode, env_file, "exec") + ["-T", "pcscf", "printenv", "DEPLOY_MODE"], check=False)
        ready = result.returncode == 0 and result.stdout.strip() == "5G" and {"scp", "pcf"}.issubset(running)
        return RealIMSCheck(
            id="ims_policy_path",
            status="PASS" if ready else "WARNING",
            message="P-CSCF N5 mode and SCP/PCF are ready" if ready else "N5 policy readiness is incomplete",
            evidence={"mode": "N5"},
        )

    def _registration_check(self, mode: Mode, env_file: Path) -> RealIMSCheck:
        logs = "\n".join(
            self._run(self._compose_command(mode, env_file, "logs") + ["--tail", "1000", service], check=False).stdout
            for service in ("pcscf", "icscf", "scscf", "pyhss")
        )
        register = re.search(r"REGISTER\s+sip:", logs, re.IGNORECASE)
        challenged = re.search(r"401\s+Unauthorized|WWW-Authenticate[:=].*AKA|MAR success - 401/407", logs, re.IGNORECASE)
        authorization = re.search(r"Authorization:.*(?:AKAv1-MD5|Digest)|ims_authenticate\(\): vector .* successfully used", logs, re.IGNORECASE)
        success = re.search(r"SAR success - 200 response sent from module|REGISTER[^\n]*(?:SIP/2\.0\s+200|200 OK)", logs, re.IGNORECASE)
        cx = re.search(r"(?:MAR|MAA|SAR|SAA|multimedia.auth|server.assignment)", logs, re.IGNORECASE)
        if all((register, challenged, authorization, success, cx)):
            return RealIMSCheck(id="authenticated_registration", status="PASS", message="Authenticated IMS registration is proven")
        if register:
            return RealIMSCheck(id="authenticated_registration", status="WARNING", message="IMS REGISTER was seen but authenticated registration evidence is incomplete")
        return RealIMSCheck(id="authenticated_registration", status="WARNING", message="No authenticated IMS registration has been observed")

    def _pyhss(self, mode: Mode, env_file: Path) -> PyHSSService:
        return PyHSSService(lambda method, path, body, query: self._pyhss_request(mode, env_file, method, path, body, query))

    def _pyhss_request(
        self,
        mode: Mode,
        env_file: Path,
        method: str,
        path: str,
        body: dict[str, Any] | None,
        query: dict[str, Any] | None,
    ) -> Any:
        key_path = self._state_dir(mode) / "provisioning.key"
        if not key_path.is_file():
            raise PyHSSError("pyHSS runtime credentials are unavailable")
        envelope = {
            "method": method,
            "path": path,
            "body": body,
            "query": query,
            "key": key_path.read_text(encoding="utf-8").strip(),
        }
        command = self._compose_command(mode, env_file, "exec") + ["-T", "pyhss", "python3", "-c", PYHSS_REQUEST_HELPER]
        result = self._run(command, input_text=json.dumps(envelope), check=False)
        if result.returncode != 0:
            raise PyHSSError(f"pyHSS {method} {path} request failed")
        payload = _last_json_value(result.stdout)
        if isinstance(payload, dict) and payload.get("_error") == "http":
            code = int(payload.get("status", 500))
            raise PyHSSError(f"pyHSS {method} {path} failed with HTTP {code}", code)
        if isinstance(payload, dict) and payload.get("_error"):
            raise PyHSSError("pyHSS API is unreachable inside the Compose project")
        return payload

    def _prepare_runtime(self, mode: Mode, mcc: str | None = None, mnc: str | None = None) -> Path:
        runtime_root = self.stack_dir / ".runtime"
        runtime_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        runtime_root.chmod(0o700)
        state_dir = self._state_dir(mode)
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        state_dir.chmod(0o700)
        values = _read_env(self.stack_dir / "env.defaults")
        if mode == "5g":
            values = {
                key: value.replace("172.22.0.", "172.23.0.").replace("172.22.0.0/24", "172.23.0.0/24")
                for key, value in values.items()
            }
            values.update({"UE_IPV4_INTERNET": "192.168.110.0/24", "UE_IPV4_IMS": "192.168.111.0/24"})
        existing_path = state_dir / "stack.env"
        if existing_path.is_file():
            existing = _read_env(existing_path)
            if mcc is not None and (existing.get("MCC") != mcc or existing.get("MNC") != mnc):
                raise RealIMSError("MCC/MNC conflict with the initialized real IMS runtime")
            values.update(existing)
        if mcc is not None:
            values.update({"MCC": mcc, "MNC": str(mnc)})

        pyhss_dir = state_dir / "pyhss"
        logs_dir = state_dir / "pyhss-logs"
        for directory in (pyhss_dir, logs_dir):
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            directory.chmod(0o700)
        source = self.images_dir / "pyhss-secure" / "runtime"
        for name in ("default_ifc.xml", "default_sh_user_data.xml", "pyhss_init.sh"):
            target = pyhss_dir / name
            shutil.copyfile(source / name, target)
            target.chmod(0o700 if name == "pyhss_init.sh" else 0o644)
        key_path = state_dir / "provisioning.key"
        if not key_path.exists():
            self._write_text(key_path, secrets.token_urlsafe(32) + "\n")
        key_path.chmod(0o600)
        config = (source / "config.yaml").read_text(encoding="utf-8")
        config = config.replace("lock_provisioning: False", "lock_provisioning: True")
        config = config.replace('provisioning_key: "hss"', f'provisioning_key: "{key_path.read_text(encoding="utf-8").strip()}"')
        config = config.replace("enable_insecure_auc: True", "enable_insecure_auc: False")
        config = config.replace("sqlalchemy_sql_echo: True", "sqlalchemy_sql_echo: False")
        self._write_text(pyhss_dir / "config.yaml", config)

        override = {
            "services": {
                "pyhss": {
                    "image": PYHSS_IMAGE,
                    "volumes": [f"{pyhss_dir}:/mnt/pyhss", f"{logs_dir}:/pyhss/log"],
                }
            }
        }
        self._write_text(state_dir / "override.yaml", yaml.safe_dump(override, sort_keys=False))
        values["LAIN5G_IMS_ENV_FILE"] = str(existing_path)
        self._write_text(existing_path, "\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
        return existing_path

    def _require_matching_runtime(self, mode: Mode, mcc: str, mnc: str) -> Path:
        env_file = self._state_dir(mode) / "stack.env"
        if not env_file.is_file():
            raise RealIMSError("real IMS mode must be started before provisioning")
        values = _read_env(env_file)
        if values.get("MCC") != mcc or values.get("MNC") != mnc:
            raise RealIMSError("MCC/MNC conflict with the running real IMS stack")
        return env_file

    def _enforce_mutual_exclusion(self, mode: Mode) -> None:
        other: Mode = "5g" if mode == "4g" else "4g"
        result = self._run(["docker", "compose", "ls", "--format", "json"], check=False)
        try:
            projects = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            projects = []
        other_project = self._project_name(other)
        if any(isinstance(item, dict) and item.get("Name") == other_project and "running" in str(item.get("Status", "")).lower() for item in projects):
            raise RealIMSError(f"real IMS {other} mode is already running")

    def _compose_command(self, mode: Mode, env_file: Path, action: str) -> list[str]:
        self._validate_mode(mode)
        if action not in ALLOWED_COMPOSE_ACTIONS:
            raise RealIMSError("real IMS Compose action is not allowlisted")
        env_file = self._confined(env_file)
        return [
            "docker",
            "compose",
            "-p",
            self._project_name(mode),
            "--env-file",
            str(env_file),
            "-f",
            str(self._manifest(mode)),
            "-f",
            str(self._state_dir(mode) / "override.yaml"),
            action,
        ]

    def _services(self, mode: Mode) -> list[str]:
        ims = ["mongo", "dns", "rtpengine", "mysql", "pyhss", "icscf", "scscf", "pcscf"]
        if mode == "4g":
            return [*ims, "hss", "pcrf", "smf", "upf", "sgwc", "sgwu", "mme"]
        return [*ims, "nrf", "scp", "ausf", "udr", "udm", "pcf", "bsf", "nssf", "smf", "upf", "amf"]

    def _run(
        self,
        command: list[str],
        *,
        input_text: str | None = None,
        check: bool = True,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self._validate_command(command)
        cwd = self.stack_dir if self.stack_dir.is_dir() else self.project_root
        self._confined(cwd)
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=os.environ.copy(),
                input=input_text,
                text=True,
                capture_output=True,
                timeout=timeout or self.settings.command_timeout,
                check=False,
                shell=False,
            )
        except FileNotFoundError as exc:
            if check:
                raise RealIMSError("real IMS command could not be executed") from exc
            return subprocess.CompletedProcess(command, 127, "", "command unavailable")
        except subprocess.TimeoutExpired as exc:
            if check:
                raise RealIMSError("real IMS command timed out") from exc
            return subprocess.CompletedProcess(command, 124, "", "command timed out")
        if check and result.returncode != 0:
            raise RealIMSError(f"real IMS command failed with exit code {result.returncode}")
        return result

    def _pyhss_is_unpublished(self, manifest: Path) -> bool:
        try:
            document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return False
        pyhss = (document.get("services") or {}).get("pyhss") if isinstance(document, dict) else None
        return isinstance(pyhss, dict) and not pyhss.get("ports")

    def _write_text(self, path: Path, value: str) -> None:
        path = self._confined(path)
        path.write_text(value, encoding="utf-8")
        path.chmod(0o600)

    def _write_json(self, path: Path, value: dict[str, Any]) -> None:
        self._write_text(path, json.dumps(value, indent=2) + "\n")

    def _state_dir(self, mode: Mode) -> Path:
        self._validate_mode(mode)
        return self._confined(self.stack_dir / ".runtime" / mode)

    def _manifest(self, mode: Mode) -> Path:
        self._validate_mode(mode)
        return self._confined(self.stack_dir / f"compose.{mode}.yaml")

    def _validate_command(self, command: list[str]) -> None:
        if not command or command[0] != "docker" or len(command) < 2 or command[1] not in ALLOWED_DOCKER_SUBCOMMANDS:
            raise RealIMSError("real IMS command is not allowlisted")
        if any(not isinstance(argument, str) or "\x00" in argument for argument in command):
            raise RealIMSError("real IMS command contains an invalid argument")
        if command[1] == "compose":
            self._validate_compose_command(command)
        elif command[1] == "image":
            if len(command) != 4 or command[2] != "inspect" or command[3] not in FIRST_PARTY_IMAGES:
                raise RealIMSError("real IMS image command is not allowlisted")
        elif len(command) != 5 or command[2] != "-t" or command[3] not in FIRST_PARTY_IMAGES:
            raise RealIMSError("real IMS build command is not allowlisted")
        elif self._confined(Path(command[4])) != self._confined(self.images_dir / FIRST_PARTY_IMAGES[command[3]]):
            raise RealIMSError("real IMS build context is not allowlisted")
        for argument in command[1:]:
            if Path(argument).is_absolute():
                self._confined(Path(argument))

    def _validate_compose_command(self, command: list[str]) -> None:
        index = 2
        while index < len(command):
            argument = command[index]
            if argument in COMPOSE_OPTIONS_WITH_VALUE:
                if index + 1 >= len(command):
                    raise RealIMSError("real IMS Compose option is missing a value")
                if argument in COMPOSE_PATH_OPTIONS:
                    path = Path(command[index + 1])
                    self._confined(path if path.is_absolute() else self.stack_dir / path)
                index += 2
                continue
            if argument.startswith("-") or argument not in ALLOWED_COMPOSE_ACTIONS:
                raise RealIMSError("real IMS Compose command is not allowlisted")
            return
        raise RealIMSError("real IMS Compose action is required")

    def _confined(self, path: Path) -> Path:
        resolved = path.resolve()
        if resolved != self.project_root and self.project_root not in resolved.parents:
            raise RealIMSError("real IMS path is outside the project root")
        return resolved

    @staticmethod
    def _project_name(mode: Mode) -> str:
        return f"lain5g-lab-ims-real-{mode}"

    @staticmethod
    def _validate_mode(mode: str) -> None:
        if mode not in {"4g", "5g"}:
            raise RealIMSError("real IMS mode must be 4g or 5g")

    @staticmethod
    def _check(check_id: str, passed: bool, message: str) -> RealIMSCheck:
        return RealIMSCheck(id=check_id, status="PASS" if passed else "FAIL", message=message)

    @staticmethod
    def _report(mode: Mode, checks: list[RealIMSCheck]) -> RealIMSStatusReport:
        status = "FAIL" if any(item.status == "FAIL" for item in checks) else "WARNING" if any(item.status == "WARNING" for item in checks) else "PASS"
        return RealIMSStatusReport(mode=mode, status=status, checks=checks)


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def _open5gs_document(subscriber: RealIMSSubscriber) -> dict[str, Any]:
    def session(name: str, qci: int, voice: bool = False) -> dict[str, Any]:
        value: dict[str, Any] = {
            "name": name,
            "type": 3,
            "pcc_rule": [],
            "ambr": {"downlink": {"value": 1, "unit": 3}, "uplink": {"value": 1, "unit": 3}},
            "qos": {"index": qci, "arp": {"priority_level": 1 if voice else 8, "pre_emption_capability": 1, "pre_emption_vulnerability": 1}},
        }
        if voice:
            value["pcc_rule"] = [_pcc_rule(1, 2, 128), _pcc_rule(2, 4, 812)]
        return value

    return {
        "schema_version": 1,
        "imsi": subscriber.imsi,
        "supi": subscriber.imsi,
        "msisdn": [subscriber.msisdn],
        "imeisv": [],
        "mme_host": [],
        "mme_realm": [],
        "purge_flag": [],
        "access_restriction_data": 32,
        "subscriber_status": 0 if subscriber.enabled else 1,
        "operator_determined_barring": 2,
        "network_access_mode": 0,
        "subscribed_rau_tau_timer": 12,
        "security": {"k": subscriber.ki, "amf": subscriber.amf, "op": None, "opc": subscriber.opc, "sqn": subscriber.sqn_hex},
        "ambr": {"downlink": {"value": 1, "unit": 3}, "uplink": {"value": 1, "unit": 3}},
        "slice": [{"sst": 1, "default_indicator": True, "session": [session(subscriber.apn_internet, 9), session(subscriber.apn_ims, 5, True)]}],
        "__v": 0,
    }


def _pcc_rule(qci: int, priority: int, rate: int) -> dict[str, Any]:
    return {
        "flow": [],
        "qos": {
            "index": qci,
            "arp": {"priority_level": priority, "pre_emption_capability": 2, "pre_emption_vulnerability": 2},
            "mbr": {"downlink": {"value": rate, "unit": 1}, "uplink": {"value": rate, "unit": 1}},
            "gbr": {"downlink": {"value": rate, "unit": 1}, "uplink": {"value": rate, "unit": 1}},
        },
    }


def _running_services(raw: str) -> set[str]:
    try:
        parsed = json.loads(raw)
        items = parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        items = []
        for line in raw.splitlines():
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {
        str(item["Service"])
        for item in items
        if isinstance(item, dict) and item.get("Service") and str(item.get("State", "")).lower() == "running"
    }


def _last_json_value(raw: str) -> Any:
    for line in reversed(raw.splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise PyHSSError("pyHSS returned an invalid response")


def _last_json_object(raw: str) -> dict[str, Any]:
    for line in reversed(raw.splitlines()):
        candidate = line[line.find("{") :] if "{" in line else line
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise RealIMSError("Open5GS did not return a reconciliation result")


def _last_json_array(raw: str) -> list[dict[str, Any]]:
    for line in reversed(raw.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    raise RealIMSError("Open5GS did not return a subscriber list")


def _open5gs_apns(record: dict[str, Any] | None) -> list[str]:
    if not record:
        return []
    names: set[str] = set()
    for slice_item in record.get("slice", []):
        if not isinstance(slice_item, dict):
            continue
        for session in slice_item.get("session", []):
            if isinstance(session, dict) and session.get("name"):
                names.add(str(session["name"]))
    return sorted(names)


def _last_integer(raw: str) -> int:
    for line in reversed(raw.splitlines()):
        match = re.fullmatch(r"(?:[^>]*>\s*)?([0-9]+)\s*", line)
        if match:
            return int(match.group(1))
    return 0
