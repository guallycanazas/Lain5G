#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from _common import ROOT, relative, source_files


STRUCTURED_SUFFIXES = {".json", ".yaml", ".yml"}
SBOM_SUFFIXES = STRUCTURED_SUFFIXES | {".spdx", ".xml"}
REQUIRED_RELEASE_FILES = (
    "AUTHORS.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE",
    "README.md",
    "SUPPORT.md",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "codemeta.json",
    "docs/release/sbom-status.md",
)


def _structured(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream) if path.suffix.lower() == ".json" else yaml.safe_load(stream)


def _citation(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        value = _structured(path)
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return [f"CITATION.cff is not valid YAML ({type(exc).__name__})"]
    if not isinstance(value, Mapping):
        return ["CITATION.cff must contain a mapping"]
    if not re.fullmatch(r"1\.\d+\.\d+", str(value.get("cff-version", ""))):
        errors.append("CITATION.cff has no valid cff-version")
    for field in ("message", "title"):
        if not str(value.get(field, "")).strip():
            errors.append(f"CITATION.cff is missing {field}")
    authors = value.get("authors")
    if not isinstance(authors, list) or not authors:
        errors.append("CITATION.cff must list at least one author")
    elif any(not isinstance(author, Mapping) or not (author.get("family-names") or author.get("name")) for author in authors):
        errors.append("CITATION.cff contains an author without family-names or name")
    release_version = value.get("version")
    expected_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if release_version is not None and str(release_version) != expected_version:
        errors.append(f"CITATION.cff version does not match VERSION ({expected_version})")
    released = value.get("date-released")
    if released is not None:
        try:
            date.fromisoformat(str(released))
        except ValueError:
            errors.append("CITATION.cff date-released is not an ISO date")
    return errors


def _codemeta(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        value = _structured(path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"codemeta.json is not valid JSON ({type(exc).__name__})"]
    if not isinstance(value, Mapping):
        return ["codemeta.json must contain an object"]
    expected_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    expected_repository = "https://github.com/guallycanazas/Lain5G"
    if value.get("version") != expected_version:
        errors.append(f"codemeta.json version does not match VERSION ({expected_version})")
    if value.get("codeRepository") != expected_repository:
        errors.append("codemeta.json codeRepository does not identify the project repository")
    if value.get("license") != "https://spdx.org/licenses/MIT":
        errors.append("codemeta.json does not identify the MIT license")
    authors = value.get("author")
    if not isinstance(authors, list) or not authors:
        errors.append("codemeta.json must contain a non-empty author list")
    return errors


def _sbom(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".xml":
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            return [f"{relative(path)} is not valid XML ({type(exc).__name__})"]
        if root.tag.rsplit("}", 1)[-1] != "bom":
            return [f"{relative(path)} is not a CycloneDX XML BOM"]
        return []
    if suffix == ".spdx":
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return [f"{relative(path)} cannot be read ({type(exc).__name__})"]
        required = ("SPDXVersion: SPDX-", "DataLicense: CC0-1.0", "SPDXID: SPDXRef-DOCUMENT")
        return [] if all(marker in text for marker in required) else [f"{relative(path)} is not a valid SPDX tag-value document"]

    try:
        value = _structured(path)
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return [f"{relative(path)} is not a valid structured SBOM ({type(exc).__name__})"]
    if not isinstance(value, Mapping):
        return [f"{relative(path)} must contain an SBOM mapping"]
    if value.get("bomFormat") == "CycloneDX":
        valid = bool(value.get("specVersion")) and isinstance(value.get("components", []), list)
        return [] if valid else [f"{relative(path)} has incomplete CycloneDX metadata"]
    if str(value.get("spdxVersion", "")).startswith("SPDX-"):
        valid = (
            value.get("dataLicense") == "CC0-1.0"
            and value.get("SPDXID") == "SPDXRef-DOCUMENT"
            and bool(value.get("documentNamespace"))
            and isinstance(value.get("packages", []), list)
        )
        return [] if valid else [f"{relative(path)} has incomplete SPDX metadata"]
    return [f"{relative(path)} is neither a CycloneDX nor SPDX SBOM"]


def _is_sbom_status(path: Path) -> bool:
    name = path.name.lower()
    return "sbom" in name and "status" in name or name.startswith("status.") and "sbom" in {part.lower() for part in path.parts}


def _status_artifact(path: Path) -> tuple[Path | None, list[str]]:
    try:
        value = _structured(path)
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return None, [f"{relative(path)} is not a valid SBOM status ({type(exc).__name__})"]
    if not isinstance(value, Mapping) or not str(value.get("status", "")).strip():
        return None, [f"{relative(path)} must contain a non-empty status"]
    artifact = value.get("artifact")
    if artifact is None:
        return None, []
    candidate = (path.parent / str(artifact)).resolve()
    if candidate != ROOT and ROOT not in candidate.parents:
        return None, [f"{relative(path)} references an artifact outside the repository"]
    if not candidate.is_file():
        return None, [f"{relative(path)} references a missing artifact"]
    return candidate, []


def _markdown_status_artifact(path: Path) -> tuple[Path | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, [f"{relative(path)} cannot be read ({type(exc).__name__})"]
    artifact_match = re.search(r"^- Path: `([^`]+)`\s*$", text, re.MULTILINE)
    digest_match = re.search(r"^- SHA-256:\s*\n\s*`([0-9a-f]{64})`\s*$", text, re.MULTILINE)
    if artifact_match is None or digest_match is None:
        return None, [f"{relative(path)} must declare an artifact path and SHA-256"]
    candidate = (ROOT / artifact_match.group(1)).resolve()
    if candidate != ROOT and ROOT not in candidate.parents:
        return None, [f"{relative(path)} references an artifact outside the repository"]
    if not candidate.is_file():
        return None, [f"{relative(path)} references a missing artifact"]
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual != digest_match.group(1):
        return None, [f"{relative(path)} SBOM SHA-256 does not match {relative(candidate)}"]
    return candidate, []


def main() -> int:
    files = source_files()
    errors: list[str] = []
    for required in REQUIRED_RELEASE_FILES:
        if not (ROOT / required).is_file():
            errors.append(f"required release file is missing: {required}")

    citation = ROOT / "CITATION.cff"
    citation_state = "not present"
    if citation.is_file():
        errors.extend(_citation(citation))
        citation_state = "validated"

    codemeta = ROOT / "codemeta.json"
    codemeta_state = "not present"
    if codemeta.is_file():
        errors.extend(_codemeta(codemeta))
        codemeta_state = "validated"

    statuses = {
        path for path in files if path.suffix.lower() in STRUCTURED_SUFFIXES and _is_sbom_status(path)
    }
    artifacts = {
        path
        for path in files
        if path.suffix.lower() in SBOM_SUFFIXES
        and not _is_sbom_status(path)
        and ("sbom" in path.name.lower() or "sbom" in {part.lower() for part in path.parts})
    }
    for status in sorted(statuses):
        artifact, status_errors = _status_artifact(status)
        errors.extend(status_errors)
        if artifact is not None:
            artifacts.add(artifact)

    markdown_status = ROOT / "docs/release/sbom-status.md"
    markdown_status_count = 0
    if markdown_status.is_file():
        artifact, status_errors = _markdown_status_artifact(markdown_status)
        errors.extend(status_errors)
        markdown_status_count = 1
        if artifact is not None:
            artifacts.add(artifact)
    for artifact in sorted(artifacts):
        errors.extend(_sbom(artifact))

    if errors:
        print(f"release-artifacts: FAIL ({len(errors)} error(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    status_count = len(statuses) + markdown_status_count
    sbom_state = f"{len(artifacts)} artifact(s), {status_count} status file(s) validated" if artifacts or status_count else "not present"
    print(
        "release-artifacts: OK "
        f"(CITATION.cff {citation_state}; codemeta.json {codemeta_state}; SBOM {sbom_state})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
