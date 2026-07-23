#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Any

from _common import ROOT, relative, source_files

RESULTS_SCRIPT_DIR = ROOT / "scripts" / "results"
if str(RESULTS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(RESULTS_SCRIPT_DIR))

from public_result import (  # noqa: E402
    CRITERION_OUTCOMES,
    ENVIRONMENT_FIELDS,
    EXECUTION_STATUSES,
    RESULT_CLASSIFICATIONS,
    RESULT_FIELDS,
    SCENARIOS,
    PublicResultError,
    load_json_file,
    normalized_json,
    scan_text,
    scan_value,
    validate_environment_summary,
    validate_public_result,
)


PUBLIC_PREFIX = "results/public/"
PUBLIC_ROOT = ROOT / "results" / "public"
RESULT_SCHEMA = PUBLIC_ROOT / "public-result.schema.json"
ENVIRONMENT_SCHEMA = PUBLIC_ROOT / "environment-summary.schema.json"
REQUIRED_ROOT_FILES = {
    "results/public/README.md",
    "results/public/environment-summary.schema.json",
    "results/public/public-result.schema.json",
}
RESULT_DIRECTORIES = set(SCENARIOS)
SUPPORT_DIRECTORIES = {"summaries", "tables"}
REQUIRED_DIRECTORIES = {"environment"} | RESULT_DIRECTORIES | SUPPORT_DIRECTORIES
SAFE_NAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}\Z")


def _load(path: Path) -> Any:
    return load_json_file(path)


def _schema_errors() -> list[str]:
    errors: list[str] = []
    try:
        result_schema = _load(RESULT_SCHEMA)
    except PublicResultError as exc:
        errors.append(f"results/public/public-result.schema.json: {exc}")
        result_schema = None
    try:
        environment_schema = _load(ENVIRONMENT_SCHEMA)
    except PublicResultError as exc:
        errors.append(f"results/public/environment-summary.schema.json: {exc}")
        environment_schema = None

    if not isinstance(result_schema, dict):
        if result_schema is not None:
            errors.append("results/public/public-result.schema.json: schema must be an object")
    else:
        properties = result_schema.get("properties")
        required = result_schema.get("required")
        if result_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append("results/public/public-result.schema.json: unsupported JSON Schema draft")
        if result_schema.get("additionalProperties") is not False:
            errors.append("results/public/public-result.schema.json: additional properties must be disabled")
        if not isinstance(required, list) or any(not isinstance(field, str) for field in required):
            errors.append("results/public/public-result.schema.json: required fields must be a string array")
        elif set(required) != RESULT_FIELDS:
            errors.append("results/public/public-result.schema.json: required fields differ from the exporter")
        if not isinstance(properties, dict) or set(properties) != RESULT_FIELDS:
            errors.append("results/public/public-result.schema.json: properties differ from the exporter")
        else:
            if properties.get("source_commit", {}).get("pattern") != "^[0-9a-f]{40}$":
                errors.append("results/public/public-result.schema.json: source commit is not exactly 40 hex characters")
            if tuple(properties.get("scenario", {}).get("enum", [])) != SCENARIOS:
                errors.append("results/public/public-result.schema.json: scenario values differ from the exporter")
            if tuple(properties.get("result_classification", {}).get("enum", [])) != RESULT_CLASSIFICATIONS:
                errors.append("results/public/public-result.schema.json: classifications differ from the exporter")
            if tuple(properties.get("execution_status", {}).get("enum", [])) != EXECUTION_STATUSES:
                errors.append("results/public/public-result.schema.json: execution statuses differ from the exporter")
            definitions = result_schema.get("$defs")
            criterion = (
                definitions.get("criterion", {}).get("properties", {})
                if isinstance(definitions, dict) and isinstance(definitions.get("criterion"), dict)
                else {}
            )
            if not isinstance(criterion, dict):
                criterion = {}
            if tuple(criterion.get("outcome", {}).get("enum", [])) != CRITERION_OUTCOMES:
                errors.append("results/public/public-result.schema.json: criterion outcomes differ from the exporter")

    if not isinstance(environment_schema, dict):
        if environment_schema is not None:
            errors.append("results/public/environment-summary.schema.json: schema must be an object")
    else:
        properties = environment_schema.get("properties")
        required = environment_schema.get("required")
        if environment_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append("results/public/environment-summary.schema.json: unsupported JSON Schema draft")
        if environment_schema.get("additionalProperties") is not False:
            errors.append("results/public/environment-summary.schema.json: additional properties must be disabled")
        if not isinstance(required, list) or any(not isinstance(field, str) for field in required):
            errors.append("results/public/environment-summary.schema.json: required fields must be a string array")
        elif set(required) != ENVIRONMENT_FIELDS:
            errors.append("results/public/environment-summary.schema.json: required fields differ from the verifier")
        if not isinstance(properties, dict) or set(properties) != ENVIRONMENT_FIELDS:
            errors.append("results/public/environment-summary.schema.json: properties differ from the verifier")
    return errors


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PublicResultError("public text artifact is not readable UTF-8") from exc


def _validate_markdown(path: Path) -> None:
    text = _text(path)
    if not text or not text.endswith("\n") or "\r" in text:
        raise PublicResultError("public Markdown must be non-empty normalized text")
    scan_text(text, multiline=True)


def _validate_csv(path: Path) -> None:
    text = _text(path)
    if not text or not text.endswith("\n") or "\r" in text:
        raise PublicResultError("public CSV must be non-empty normalized text")
    scan_text(text, multiline=True)
    try:
        rows = list(csv.reader(text.splitlines()))
    except csv.Error as exc:
        raise PublicResultError("public CSV is not parseable") from exc
    if len(rows) < 2 or not rows[0] or any(not heading for heading in rows[0]):
        raise PublicResultError("public CSV must contain a header and at least one data row")
    if len(set(rows[0])) != len(rows[0]) or any(len(row) != len(rows[0]) for row in rows):
        raise PublicResultError("public CSV columns are inconsistent")
    for row in rows:
        for cell in row:
            if len(cell) > 500 or cell.startswith(("=", "+", "-", "@")):
                raise PublicResultError("public CSV contains an unsafe cell")
            scan_text(cell)


def _validate_support_json(path: Path) -> None:
    value = _load(path)
    scan_value(value)
    if path.read_bytes() != normalized_json(value):
        raise PublicResultError("public JSON is not deterministically normalized")


def _direct_members(public_files: dict[str, Path], directory: str) -> dict[str, Path]:
    prefix = f"results/public/{directory}/"
    return {
        rel: path
        for rel, path in public_files.items()
        if rel.startswith(prefix) and "/" not in rel[len(prefix) :]
    }


def _path_parts(path: str) -> tuple[str, ...]:
    return tuple(part for part in path.split("/") if part)


def main() -> int:
    errors: list[str] = []
    try:
        files = source_files()
    except RuntimeError as exc:
        print(f"public-results: FAIL ({exc})", file=sys.stderr)
        return 1
    public_files = {
        relative(path): path
        for path in files
        if relative(path).startswith(PUBLIC_PREFIX)
    }

    for directory in sorted(REQUIRED_DIRECTORIES):
        if not (PUBLIC_ROOT / directory).is_dir():
            errors.append(f"results/public/{directory}: required directory is missing")
    for required in sorted(REQUIRED_ROOT_FILES):
        if required not in public_files:
            errors.append(f"{required}: required public artifact is missing")

    for rel, path in sorted(public_files.items()):
        nested = rel[len(PUBLIC_PREFIX) :]
        parts = _path_parts(nested)
        if len(parts) == 1:
            if rel not in REQUIRED_ROOT_FILES:
                errors.append(f"{rel}: unsupported artifact at the public root")
        elif len(parts) == 2:
            if parts[0] not in REQUIRED_DIRECTORIES:
                errors.append(f"{rel}: unsupported public directory")
        else:
            errors.append(f"{rel}: nested public artifact directories are not allowed")
        try:
            if path.stat().st_size > 1024 * 1024:
                raise PublicResultError("public artifact exceeds the size limit")
            if path.name == ".gitkeep":
                if path.read_bytes() != b"":
                    raise PublicResultError(".gitkeep must be empty")
            elif path.suffix.lower() in {".md", ".csv"}:
                scan_text(_text(path), multiline=True)
            elif path.suffix.lower() == ".json":
                scan_value(_load(path))
            else:
                raise PublicResultError("public artifact type is not allowed")
        except (OSError, PublicResultError) as exc:
            errors.append(f"{rel}: {exc}")

    errors.extend(_schema_errors())

    environment_count = 0
    for rel, path in sorted(_direct_members(public_files, "environment").items()):
        if path.name == ".gitkeep":
            errors.append(f"{rel}: environment is not an empty placeholder directory")
            continue
        if path.suffix != ".json" or SAFE_NAME_RE.fullmatch(path.name) is None:
            errors.append(f"{rel}: environment summary filename is invalid")
            continue
        try:
            value = _load(path)
            validate_environment_summary(value, root=ROOT)
            if path.read_bytes() != normalized_json(value):
                raise PublicResultError("environment summary is not deterministically normalized")
        except (OSError, PublicResultError) as exc:
            errors.append(f"{rel}: {exc}")
        else:
            environment_count += 1
    if environment_count == 0:
        errors.append("results/public/environment: at least one environment summary is required")

    result_count = 0
    for scenario in SCENARIOS:
        members = _direct_members(public_files, scenario)
        artifacts = {rel: path for rel, path in members.items() if path.name != ".gitkeep"}
        placeholder = f"results/public/{scenario}/.gitkeep"
        if artifacts and placeholder in members:
            errors.append(f"{placeholder}: placeholder must be removed when results exist")
        if not artifacts and placeholder not in members:
            errors.append(f"{placeholder}: empty result directory requires a placeholder")
        for rel, path in sorted(artifacts.items()):
            if path.suffix != ".json" or SAFE_NAME_RE.fullmatch(path.name) is None:
                errors.append(f"{rel}: scenario result filename is invalid")
                continue
            try:
                value = _load(path)
                validate_public_result(value, root=ROOT, expected_scenario=scenario)
                if path.name != f"{value['run_id']}.json":
                    raise PublicResultError("scenario result filename does not match its run ID")
                if path.read_bytes() != normalized_json(value):
                    raise PublicResultError("scenario result is not deterministically normalized")
            except (OSError, PublicResultError) as exc:
                errors.append(f"{rel}: {exc}")
            else:
                result_count += 1

    support_count = 0
    for directory in sorted(SUPPORT_DIRECTORIES):
        members = _direct_members(public_files, directory)
        artifacts = {rel: path for rel, path in members.items() if path.name != ".gitkeep"}
        placeholder = f"results/public/{directory}/.gitkeep"
        if artifacts and placeholder in members:
            errors.append(f"{placeholder}: placeholder must be removed when public artifacts exist")
        if not artifacts and placeholder not in members:
            errors.append(f"{placeholder}: empty public artifact directory requires a placeholder")
        allowed = {".csv", ".json"} if directory == "tables" else {".json", ".md"}
        for rel, path in sorted(artifacts.items()):
            if path.suffix.lower() not in allowed or SAFE_NAME_RE.fullmatch(path.name) is None:
                errors.append(f"{rel}: support artifact filename or format is invalid")
                continue
            try:
                if path.suffix.lower() == ".json":
                    _validate_support_json(path)
                elif path.suffix.lower() == ".csv":
                    _validate_csv(path)
                else:
                    _validate_markdown(path)
            except (OSError, PublicResultError) as exc:
                errors.append(f"{rel}: {exc}")
            else:
                support_count += 1

    readme = PUBLIC_ROOT / "README.md"
    if readme.is_file():
        try:
            _validate_markdown(readme)
        except PublicResultError as exc:
            errors.append(f"results/public/README.md: {exc}")

    if errors:
        print(f"public-results: FAIL ({len(errors)} error(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "public-results: OK "
        f"({result_count} scenario result(s); {environment_count} environment summary(s); "
        f"{support_count} support artifact(s))"
    )
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
