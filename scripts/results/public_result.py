from __future__ import annotations

import hashlib
import ipaddress
import json
import math
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "1.0"
SCENARIOS = ("4g-lte-sim", "4g-ims-sim", "5g-sa-sim", "5g-vonr-sim")
RESULT_CLASSIFICATIONS = (
    "VALIDATED",
    "PARTIALLY_VALIDATED",
    "NOT_VALIDATED",
    "SIMULATION_ONLY",
    "DRY_RUN_ONLY",
)
EXECUTION_STATUSES = ("PASS", "FAIL", "BLOCKED", "SKIPPED")
CRITERION_OUTCOMES = ("MET", "NOT_MET", "NOT_ASSESSED")
RESULT_FIELDS = {
    "artifact_type",
    "schema_version",
    "run_id",
    "started_at_utc",
    "ended_at_utc",
    "source_commit",
    "release_version",
    "scenario",
    "command_label",
    "public_configurations",
    "environment_reference",
    "success_criteria",
    "result_classification",
    "execution_status",
    "duration_seconds",
    "limitations",
    "associated_files",
}
ENVIRONMENT_FIELDS = {
    "artifact_type",
    "schema_version",
    "captured_at_utc",
    "source_commit",
    "release_version",
    "scope",
    "tools",
    "limitations",
}
MAX_INPUT_BYTES = 256 * 1024
MAX_PUBLIC_FILE_BYTES = 1024 * 1024

_RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_VERSION_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+-]{0,63}\Z")
_UTC_RE = re.compile(
    r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
    r"T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,6})?Z\Z"
)
_COMMAND_LABEL_RE = re.compile(
    r"(?!.* {2})[A-Za-z0-9](?:[A-Za-z0-9 ._()+:-]{0,78}[A-Za-z0-9._()+:-])?\Z"
)
_PRINTABLE_ASCII_RE = re.compile(r"[\x20-\x7e]*\Z")
_SAFE_TOOL_VERSION_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z ._()+:-]{0,79}\Z")
_IPV4_RE = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
_BRACKETED_IPV6_RE = re.compile(r"\[([0-9A-Fa-f:.]+)(?:%[A-Za-z0-9_.-]+)?\]")
_IPV6_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])")
_SECRET_VALUE_RE = re.compile(
    r"(?i)\b(?:password|passwd|passphrase|secret|token|api[ _-]?key|"
    r"credential|authorization|client[ _-]?secret|ki|opc)\s*[:=]\s*\S+"
)
_AUTH_VALUE_RE = re.compile(r"(?i)\b(?:basic|bearer)\s+[A-Za-z0-9._~+/=-]{8,}")
_CREDENTIAL_URI_RE = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@")
_JWT_RE = re.compile(r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
_PROVIDER_TOKEN_RES = (
    re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,}(?![A-Za-z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{20,}(?![A-Za-z0-9])"),
)
_SIM_LABEL_RE = re.compile(
    r"(?i)\b(?:imsi|iccid|supi|suci|msisdn|imei)\s*[:=#]\s*[A-Za-z0-9:+-]{5,}"
)
_SIM_DIGITS_RE = re.compile(r"(?<!\d)\d{11,16}(?!\d)")
_RF_VALUE_RE = re.compile(
    r"(?i)\b(?:n?r[-_ ]?arfcn|earfcn|center[-_ ]?frequency|tx[-_ ]?gain|"
    r"rx[-_ ]?gain|tx[-_ ]?power|sample[-_ ]?rate|channel[-_ ]?plan|"
    r"rf[-_ ]?plan)\s*[:=#]\s*\S+"
)
_RF_UNIT_RE = re.compile(r"(?i)(?<![A-Za-z0-9])\d+(?:\.\d+)?\s*(?:hz|khz|mhz|ghz|dbm)(?![A-Za-z0-9])")
_RF_NUMBER_RE = re.compile(
    r"(?i)\b(?:n?r[-_ ]?arfcn|earfcn|center[-_ ]?frequency|tx[-_ ]?gain|"
    r"rx[-_ ]?gain|tx[-_ ]?power|sample[-_ ]?rate)\s+-?\d+(?:\.\d+)?\b"
)
_HARDWARE_SERIAL_RE = re.compile(
    r"(?i)\b(?:hardware[-_ ]*)?serial(?:[-_ ]*(?:number|no))?\s*[:=#]\s*[A-Za-z0-9-]{4,}"
)
_LOCAL_PATH_RE = re.compile(
    r"(?:^|[\s('\"=])(?:~[/\\]|\.\.?[/\\]|[A-Za-z]:[/\\]|\\\\|/(?!/)[A-Za-z0-9._~-])"
)
_RAW_PROTOCOL_RES = (
    re.compile(r"(?im)^(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+\S+\s+HTTP/\d(?:\.\d)?\s*$"),
    re.compile(r"(?im)^HTTP/\d(?:\.\d)?\s+\d{3}\b"),
    re.compile(r"(?i)\bSIP/2\.0\b"),
    re.compile(r"(?i)\b(?:NGAP|NAS|GTP-U|DIAMETER)\s+(?:payload|message)\b"),
    re.compile(r"(?m)(?:\b[0-9A-Fa-f]{2}[ :]?){16,}"),
    re.compile(r"(?i)^\d{4}-\d{2}-\d{2}[T ]\S+\s+(?:TRACE|DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL)\b"),
)

_SECRET_FIELD_NAMES = {
    "access_key",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "client_secret",
    "cookie",
    "credential",
    "credentials",
    "k",
    "ki",
    "opc",
    "passphrase",
    "passwd",
    "password",
    "private_key",
    "secret",
    "secret_key",
    "secrets",
    "set_cookie",
    "token",
    "tokens",
}
_SIM_FIELD_NAMES = {"iccid", "imei", "imsi", "msisdn", "suci", "supi"}
_RF_FIELD_NAMES = {
    "antenna",
    "arfcn",
    "band",
    "bandwidth",
    "center_frequency",
    "channel_plan",
    "earfcn",
    "frequency",
    "frequencies",
    "mcc",
    "mnc",
    "nrarfcn",
    "nr_arfcn",
    "rf",
    "rf_plan",
    "rx_gain",
    "sample_rate",
    "tx_gain",
    "tx_power",
}
_HARDWARE_FIELD_NAMES = {
    "device_id",
    "device_serial",
    "fpga_id",
    "hardware_id",
    "hardware_serial",
    "serial",
    "serial_no",
    "serial_number",
    "serialnumber",
    "uhd_args",
}
_RAW_FIELD_NAMES = {
    "capture",
    "dump",
    "log",
    "logs",
    "packet_capture",
    "packets",
    "payload",
    "pcap",
    "protocol_payload",
    "raw",
    "raw_log",
    "stderr",
    "stdout",
    "trace",
}
_PROHIBITED_PATH_PARTS = {
    ".env",
    "capture",
    "captures",
    "credential",
    "credentials",
    "dump",
    "dumps",
    "env",
    "hardware",
    "log",
    "logs",
    "packet",
    "packets",
    "payload",
    "pcap",
    "private",
    "raw",
    "rf",
    "secret",
    "secrets",
    "serial",
    "token",
    "tokens",
    "trace",
    "traces",
    "uhd",
    "usrp",
    "x310",
}
_PROHIBITED_SUFFIXES = {
    ".cap",
    ".db",
    ".dump",
    ".env",
    ".key",
    ".log",
    ".pcap",
    ".pcapng",
    ".pem",
    ".sqlite",
    ".sqlite3",
}


class PublicResultError(ValueError):
    """A validation failure whose message is safe to show without input data."""


def normalized_json(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise PublicResultError("input is not deterministic JSON data") from exc
    return f"{text}\n".encode("ascii")


def _no_duplicate_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PublicResultError("input contains duplicate fields")
        result[key] = value
    return result


def load_json_bytes(raw: bytes) -> Any:
    if len(raw) > MAX_INPUT_BYTES:
        raise PublicResultError("input exceeds the public summary size limit")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicate_fields,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                PublicResultError("input contains a non-finite number")
            ),
        )
    except PublicResultError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise PublicResultError("input is not valid UTF-8 JSON") from exc


def load_json_file(path: Path) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PublicResultError("input could not be read") from exc
    return load_json_bytes(raw)


def _normalized_field_name(name: str) -> str:
    expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    return re.sub(r"[^a-z0-9]+", "_", expanded.lower()).strip("_")


def _field_rejection(name: str) -> str | None:
    normalized = _normalized_field_name(name)
    parts = set(normalized.split("_"))
    if normalized in _SECRET_FIELD_NAMES or parts & {
        "authorization",
        "credential",
        "credentials",
        "passphrase",
        "passwd",
        "password",
        "secret",
        "secrets",
        "token",
        "tokens",
    }:
        return "input contains a prohibited secret or credential field"
    if normalized in _SIM_FIELD_NAMES or parts & _SIM_FIELD_NAMES:
        return "input contains a prohibited SIM identifier field"
    if (
        normalized in _RF_FIELD_NAMES
        or normalized.startswith("rf_")
        or parts & {"arfcn", "earfcn", "frequency", "frequencies", "bandwidth"}
    ):
        return "input contains a prohibited RF operational field"
    if normalized in _HARDWARE_FIELD_NAMES or "serial" in parts:
        return "input contains a prohibited hardware identifier field"
    if (
        normalized in _RAW_FIELD_NAMES
        or normalized.startswith("raw_")
        or parts & {"capture", "dump", "log", "logs", "payload", "pcap", "stderr", "stdout", "trace"}
    ):
        return "input contains a prohibited raw-data field"
    return None


def _network_address_is_prohibited(text: str) -> bool:
    candidates = [match.group(0) for match in _IPV4_RE.finditer(text)]
    candidates.extend(match.group(1) for match in _BRACKETED_IPV6_RE.finditer(text))
    candidates.extend(match.group(0) for match in _IPV6_RE.finditer(text))
    for candidate in candidates:
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if address.is_private or address.is_loopback or address.is_link_local or address.is_unspecified:
            return True
    return bool(re.search(r"(?i)(?<![A-Za-z0-9.-])localhost(?:\.localdomain)?(?![A-Za-z0-9.-])", text))


def scan_text(text: str, *, multiline: bool = False) -> None:
    if not isinstance(text, str):
        raise PublicResultError("input contains a non-text value where text is required")
    if not multiline and len(text) > 4096:
        raise PublicResultError("input text exceeds the public summary size limit")
    if multiline:
        printable = all(character in "\n\t" or 0x20 <= ord(character) <= 0x7E for character in text)
    else:
        printable = bool(_PRINTABLE_ASCII_RE.fullmatch(text))
    if not printable:
        raise PublicResultError("input contains control or non-ASCII text")
    if "-----BEGIN" in text and "PRIVATE KEY-----" in text:
        raise PublicResultError("input contains prohibited private key material")
    if _SECRET_VALUE_RE.search(text) or _AUTH_VALUE_RE.search(text) or _CREDENTIAL_URI_RE.search(text):
        raise PublicResultError("input contains prohibited secret or credential material")
    if _JWT_RE.search(text) or any(pattern.search(text) for pattern in _PROVIDER_TOKEN_RES):
        raise PublicResultError("input contains prohibited token material")
    if _SIM_LABEL_RE.search(text) or (text.isdigit() and _SIM_DIGITS_RE.fullmatch(text)):
        raise PublicResultError("input contains a prohibited SIM identifier")
    if _network_address_is_prohibited(text):
        raise PublicResultError("input contains a prohibited private or local network address")
    if _RF_VALUE_RE.search(text) or _RF_UNIT_RE.search(text) or _RF_NUMBER_RE.search(text):
        raise PublicResultError("input contains prohibited RF operational data")
    if _HARDWARE_SERIAL_RE.search(text):
        raise PublicResultError("input contains a prohibited hardware serial")
    if re.search(r"(?i)\bfile://", text) or _LOCAL_PATH_RE.search(text):
        raise PublicResultError("input contains a prohibited absolute or local path")
    if any(pattern.search(text) for pattern in _RAW_PROTOCOL_RES):
        raise PublicResultError("input contains a prohibited raw protocol payload")


def scan_value(value: Any, *, _depth: int = 0) -> None:
    if _depth > 24:
        raise PublicResultError("input nesting exceeds the public summary limit")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise PublicResultError("input contains a non-text field name")
            rejection = _field_rejection(key)
            if rejection is not None:
                raise PublicResultError(rejection)
            scan_value(item, _depth=_depth + 1)
        return
    if isinstance(value, list):
        for item in value:
            scan_value(item, _depth=_depth + 1)
        return
    if isinstance(value, str):
        scan_text(value)
        return
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise PublicResultError("input contains a non-finite number")
        return
    raise PublicResultError("input contains an unsupported JSON value")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(64 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PublicResultError("a referenced public file could not be read") from exc
    return digest.hexdigest()


def _required_text(value: Any, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or value != value.strip():
        raise PublicResultError("input contains an invalid required text field")
    scan_text(value)
    return value


def _utc_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or _UTC_RE.fullmatch(value) is None:
        raise PublicResultError("input contains an invalid UTC timestamp")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PublicResultError("input contains an invalid UTC timestamp") from exc


def _repository_relative(reference: Any, *, allowed_prefixes: Sequence[str]) -> str:
    if not isinstance(reference, str) or not reference or len(reference) > 240:
        raise PublicResultError("input contains an invalid public file reference")
    scan_text(reference)
    if "\\" in reference or reference.startswith(("/", "./", "../", "~")) or "//" in reference:
        raise PublicResultError("input contains an invalid public file reference")
    path = PurePosixPath(reference)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise PublicResultError("input contains an invalid public file reference")
    if not any(reference.startswith(prefix) for prefix in allowed_prefixes):
        raise PublicResultError("input contains a public file reference outside its allowed area")
    lowered_parts = {_normalized_field_name(part) for part in path.parts}
    lowered_tokens = set(lowered_parts)
    for part in lowered_parts:
        lowered_tokens.update(part.split("_"))
    prohibited_plan = {"channel", "plan"} <= lowered_tokens or {"safety", "manifest"} <= lowered_tokens
    if (
        lowered_tokens & _PROHIBITED_PATH_PARTS
        or prohibited_plan
        or path.suffix.lower() in _PROHIBITED_SUFFIXES
    ):
        raise PublicResultError("input references a prohibited public file type")
    return reference


def _versionable(root: Path, reference: str) -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                os.fspath(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
                reference,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    if result.returncode != 0:
        return False
    return os.fsencode(reference) in result.stdout.split(b"\0")


def _safe_target(root: Path, reference: str, *, require_versionable: bool) -> Path:
    target = root / reference
    try:
        resolved_root = root.resolve(strict=True)
        resolved = target.resolve(strict=True)
    except OSError as exc:
        raise PublicResultError("a referenced public file is missing") from exc
    if resolved_root not in resolved.parents or not resolved.is_file() or target.is_symlink():
        raise PublicResultError("a referenced public file is not a regular repository file")
    if resolved.stat().st_size > MAX_PUBLIC_FILE_BYTES:
        raise PublicResultError("a referenced public file exceeds the size limit")
    if require_versionable and not _versionable(root, reference):
        raise PublicResultError("a referenced public file is not Git-versionable")
    return resolved


def _release_version(root: Path) -> str:
    try:
        return (root / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise PublicResultError("the repository release version could not be read") from exc


def validate_environment_summary(
    value: Any,
    *,
    root: Path = ROOT,
) -> None:
    scan_value(value)
    if not isinstance(value, Mapping) or set(value) != ENVIRONMENT_FIELDS:
        raise PublicResultError("environment summary fields do not match the public contract")
    if value["artifact_type"] != "public-environment-summary" or value["schema_version"] != SCHEMA_VERSION:
        raise PublicResultError("environment summary contract version is invalid")
    _utc_timestamp(value["captured_at_utc"])
    commit = value["source_commit"]
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
        raise PublicResultError("environment summary source commit is invalid")
    release_version = value["release_version"]
    if not isinstance(release_version, str) or _VERSION_RE.fullmatch(release_version) is None:
        raise PublicResultError("environment summary release version is invalid")
    if release_version != _release_version(root):
        raise PublicResultError("environment summary release version does not match VERSION")
    scope = _required_text(value["scope"], maximum=240)
    if "not a scenario result" not in scope.lower():
        raise PublicResultError("environment summary must state that it is not a scenario result")

    tools = value["tools"]
    if not isinstance(tools, list) or not tools:
        raise PublicResultError("environment summary must contain tool versions")
    names: list[str] = []
    for tool in tools:
        if not isinstance(tool, Mapping) or set(tool) != {"name", "version"}:
            raise PublicResultError("environment summary contains an invalid tool entry")
        name = tool["name"]
        version = tool["version"]
        if not isinstance(name, str) or _SLUG_RE.fullmatch(name) is None:
            raise PublicResultError("environment summary contains an invalid tool name")
        if not isinstance(version, str) or _SAFE_TOOL_VERSION_RE.fullmatch(version) is None:
            raise PublicResultError("environment summary contains an invalid tool version")
        scan_text(version)
        names.append(name)
    if names != sorted(set(names)):
        raise PublicResultError("environment summary tools must be unique and sorted")

    limitations = value["limitations"]
    if not isinstance(limitations, list) or not limitations:
        raise PublicResultError("environment summary must state its limitations")
    for limitation in limitations:
        _required_text(limitation, maximum=500)


def _validate_hashed_reference(
    item: Any,
    *,
    root: Path,
    allowed_prefixes: Sequence[str],
    allowed_suffixes: set[str],
    require_versionable: bool,
) -> tuple[str, Path]:
    if not isinstance(item, Mapping) or set(item) != {"reference", "sha256"}:
        raise PublicResultError("input contains an invalid hashed public reference")
    reference = _repository_relative(item["reference"], allowed_prefixes=allowed_prefixes)
    if PurePosixPath(reference).suffix.lower() not in allowed_suffixes:
        raise PublicResultError("input references an unsupported public file format")
    digest = item["sha256"]
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise PublicResultError("input contains an invalid public file hash")
    target = _safe_target(root, reference, require_versionable=require_versionable)
    if sha256_file(target) != digest:
        raise PublicResultError("a referenced public file hash does not match")
    return reference, target


def _validate_associated_file(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        value = load_json_file(path)
        scan_value(value)
        if path.read_bytes() != normalized_json(value):
            raise PublicResultError("associated public JSON is not deterministically normalized")
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PublicResultError("an associated public file is not readable UTF-8") from exc
    if not text or not text.endswith("\n") or "\r" in text:
        raise PublicResultError("associated public text is not normalized")
    scan_text(text, multiline=True)


def validate_public_result(
    value: Any,
    *,
    root: Path = ROOT,
    expected_scenario: str | None = None,
    require_versionable: bool = True,
) -> None:
    scan_value(value)
    if not isinstance(value, Mapping) or set(value) != RESULT_FIELDS:
        raise PublicResultError("input fields do not match the public result contract")
    if value["artifact_type"] != "public-scenario-result" or value["schema_version"] != SCHEMA_VERSION:
        raise PublicResultError("public result contract version is invalid")

    run_id = value["run_id"]
    if not isinstance(run_id, str) or _RUN_ID_RE.fullmatch(run_id) is None:
        raise PublicResultError("public result run ID is invalid")
    started = _utc_timestamp(value["started_at_utc"])
    ended = _utc_timestamp(value["ended_at_utc"])
    if ended < started:
        raise PublicResultError("public result UTC timestamps are out of order")

    commit = value["source_commit"]
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
        raise PublicResultError("public result source commit is invalid")
    release_version = value["release_version"]
    if not isinstance(release_version, str) or _VERSION_RE.fullmatch(release_version) is None:
        raise PublicResultError("public result release version is invalid")
    if release_version != _release_version(root):
        raise PublicResultError("public result release version does not match VERSION")

    scenario = value["scenario"]
    if scenario not in SCENARIOS or (expected_scenario is not None and scenario != expected_scenario):
        raise PublicResultError("public result scenario is invalid")
    command_label = value["command_label"]
    if (
        not isinstance(command_label, str)
        or _COMMAND_LABEL_RE.fullmatch(command_label) is None
        or command_label != command_label.strip()
        or "  " in command_label
    ):
        raise PublicResultError("public result command label is not sanitized")

    configurations = value["public_configurations"]
    if not isinstance(configurations, list) or not configurations:
        raise PublicResultError("public result must reference at least one public configuration")
    configuration_references: list[str] = []
    for item in configurations:
        reference, _target = _validate_hashed_reference(
            item,
            root=root,
            allowed_prefixes=("config/", "deployments/"),
            allowed_suffixes={".cfg", ".conf", ".ini", ".json", ".toml", ".yaml", ".yml"},
            require_versionable=require_versionable,
        )
        configuration_references.append(reference)
    if configuration_references != sorted(set(configuration_references)):
        raise PublicResultError("public configuration references must be unique and sorted")

    environment_reference = _repository_relative(
        value["environment_reference"],
        allowed_prefixes=("results/public/environment/",),
    )
    if PurePosixPath(environment_reference).suffix != ".json":
        raise PublicResultError("public result environment reference must be JSON")
    environment_path = _safe_target(root, environment_reference, require_versionable=require_versionable)
    environment = load_json_file(environment_path)
    validate_environment_summary(environment, root=root)
    if environment["source_commit"] != commit or environment["release_version"] != release_version:
        raise PublicResultError("public result and environment provenance do not match")

    classification = value["result_classification"]
    if classification not in RESULT_CLASSIFICATIONS:
        raise PublicResultError("public result classification is invalid")
    execution_status = value["execution_status"]
    if execution_status not in EXECUTION_STATUSES:
        raise PublicResultError("public result execution status is invalid")
    duration = value["duration_seconds"]
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 0:
        raise PublicResultError("public result duration is invalid")
    if abs((ended - started).total_seconds() - duration) > 0.000001:
        raise PublicResultError("public result duration does not match its UTC timestamps")

    associated = value["associated_files"]
    if not isinstance(associated, list):
        raise PublicResultError("public result associated files must be a list")
    associated_references: list[str] = []
    for item in associated:
        reference, target = _validate_hashed_reference(
            item,
            root=root,
            allowed_prefixes=("results/public/summaries/", "results/public/tables/"),
            allowed_suffixes={".csv", ".json", ".md"},
            require_versionable=require_versionable,
        )
        _validate_associated_file(target)
        associated_references.append(reference)
    if associated_references != sorted(set(associated_references)):
        raise PublicResultError("associated public file references must be unique and sorted")

    criteria = value["success_criteria"]
    if not isinstance(criteria, list) or not criteria:
        raise PublicResultError("public result must contain explicit success criteria")
    criterion_ids: list[str] = []
    for criterion in criteria:
        if not isinstance(criterion, Mapping) or set(criterion) != {
            "id",
            "description",
            "outcome",
            "evidence_references",
        }:
            raise PublicResultError("public result contains an invalid success criterion")
        criterion_id = criterion["id"]
        if not isinstance(criterion_id, str) or _SLUG_RE.fullmatch(criterion_id) is None:
            raise PublicResultError("public result contains an invalid success criterion ID")
        _required_text(criterion["description"], maximum=240)
        if criterion["outcome"] not in CRITERION_OUTCOMES:
            raise PublicResultError("public result contains an invalid success criterion outcome")
        evidence = criterion["evidence_references"]
        if not isinstance(evidence, list):
            raise PublicResultError("success criterion evidence references must be a list")
        checked_evidence: list[str] = []
        for reference in evidence:
            checked = _repository_relative(
                reference,
                allowed_prefixes=("results/public/summaries/", "results/public/tables/"),
            )
            if checked not in associated_references:
                raise PublicResultError("success criterion evidence is not an associated public file")
            checked_evidence.append(checked)
        if checked_evidence != sorted(set(checked_evidence)):
            raise PublicResultError("success criterion evidence references must be unique and sorted")
        criterion_ids.append(criterion_id)
    if criterion_ids != sorted(set(criterion_ids)):
        raise PublicResultError("success criterion IDs must be unique and sorted")

    limitations = value["limitations"]
    if not isinstance(limitations, list) or not limitations:
        raise PublicResultError("public result must state its limitations")
    for limitation in limitations:
        _required_text(limitation, maximum=500)


def export_public_result(
    value: Any,
    *,
    root: Path = ROOT,
    public_root: Path | None = None,
) -> Path:
    validate_public_result(value, root=root)
    destination_root = public_root if public_root is not None else root / "results" / "public"
    scenario_dir = destination_root / value["scenario"]
    try:
        resolved_destination = destination_root.resolve(strict=True)
        resolved_scenario = scenario_dir.resolve(strict=True)
    except OSError as exc:
        raise PublicResultError("public result destination structure is missing") from exc
    if resolved_destination not in resolved_scenario.parents or scenario_dir.is_symlink():
        raise PublicResultError("public result destination is not a safe directory")

    target = scenario_dir / f"{value['run_id']}.json"
    payload = normalized_json(value)
    placeholder = scenario_dir / ".gitkeep"
    if target.exists():
        try:
            existing = target.read_bytes()
        except OSError as exc:
            raise PublicResultError("existing public result could not be read") from exc
        if existing == payload:
            try:
                placeholder.unlink(missing_ok=True)
            except OSError as exc:
                raise PublicResultError("public result placeholder could not be removed") from exc
            return target
        raise PublicResultError("public result run ID already has different content")

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=resolved_scenario,
            prefix=".public-result-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, 0o644)
        os.replace(temporary_name, target)
        placeholder.unlink(missing_ok=True)
    except OSError as exc:
        raise PublicResultError("public result could not be written") from exc
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
    return target
