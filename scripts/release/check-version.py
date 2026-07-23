#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEMVER = re.compile(
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
GIT_COMMIT = re.compile(r"[0-9a-f]{40}")
EXACT_REQUIREMENT = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([^;\s]+)")

SOURCE_COMMITS = {
    "images/open5gs/Dockerfile": ("OPEN5GS_COMMIT",),
    "images/ueransim/Dockerfile": ("UERANSIM_COMMIT",),
    "images/srsran4g-sim/Dockerfile": ("SRSRAN_4G_COMMIT",),
    "images/srsran4g-uhd/Dockerfile": ("SRSRAN_4G_COMMIT", "UHD_COMMIT"),
    "images/srsranproject-uhd/Dockerfile": ("SRSRAN_PROJECT_COMMIT", "UHD_COMMIT"),
    "images/kamailio/Dockerfile": ("KAMAILIO_COMMIT",),
}


def _read(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read: {exc}")
        return ""


def _json(path: Path, errors: list[str]) -> dict:
    raw = _read(path, errors)
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: expected a JSON object")
        return {}
    return value


def _normalized_package(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirements(path: Path, errors: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for number, raw in enumerate(_read(path, errors).splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = EXACT_REQUIREMENT.fullmatch(line)
        if not match:
            errors.append(f"{path}:{number}: dependency must use one exact == version")
            continue
        name, version = match.groups()
        key = _normalized_package(name)
        if key in result:
            errors.append(f"{path}:{number}: duplicate dependency {name}")
        result[key] = version
    return result


def _dockerfiles(root: Path) -> list[Path]:
    ignored = {".git", ".venv", "node_modules"}
    return sorted(
        path
        for path in root.rglob("Dockerfile*")
        if path.is_file() and not ignored.intersection(path.relative_to(root).parts)
    )


def _compose_files(root: Path) -> list[Path]:
    files = set(root.glob("**/*compose*.yml")) | set(root.glob("**/*compose*.yaml"))
    return sorted(path for path in files if path.is_file())


def check(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()

    version_path = root / "VERSION"
    raw_version = _read(version_path, errors)
    version = raw_version.strip()
    if raw_version and raw_version != f"{version}\n":
        errors.append("VERSION must contain exactly one newline-terminated version")
    if not SEMVER.fullmatch(version):
        errors.append(f"VERSION is not valid SemVer: {version!r}")

    package = _json(root / "frontend/package.json", errors)
    package_lock = _json(root / "frontend/package-lock.json", errors)
    if package.get("version") != version:
        errors.append(f"frontend/package.json version {package.get('version')!r} != {version!r}")
    if package_lock.get("version") != version:
        errors.append(f"frontend/package-lock.json version {package_lock.get('version')!r} != {version!r}")
    lock_root = package_lock.get("packages", {}).get("", {}) if isinstance(package_lock.get("packages"), dict) else {}
    if lock_root.get("version") != version:
        errors.append(f"frontend/package-lock.json root package version {lock_root.get('version')!r} != {version!r}")
    for section in ("dependencies", "devDependencies"):
        if package.get(section, {}) != lock_root.get(section, {}):
            errors.append(f"frontend/package-lock.json root {section} contradicts package.json")

    main_py = _read(root / "backend/app/main.py", errors)
    model_py = _read(root / "backend/app/models/deployment.py", errors)
    version_py = _read(root / "backend/app/version.py", errors)
    if "from .version import VERSION" not in main_py or "version=VERSION" not in main_py:
        errors.append("backend FastAPI metadata must use backend.app.version.VERSION")
    if re.search(r"\bversion\s*=\s*['\"]", main_py):
        errors.append("backend FastAPI metadata contains a literal version")
    if "version: str = VERSION" not in model_py:
        errors.append("backend health output must expose VERSION")
    if ' / "VERSION"' not in version_py:
        errors.append("backend version module must read the root VERSION file")

    changelog = _read(root / "CHANGELOG.md", errors)
    if f"## [{version}] - Unreleased" not in changelog:
        errors.append(f"CHANGELOG.md is missing [{version}] - Unreleased")
    versions_doc = _read(root / "docs/versions.md", errors)
    matrix_doc = _read(root / "docs/reproducibility/version-matrix.md", errors)
    policy_doc = _read(root / "docs/reproducibility/dependency-policy.md", errors)
    for path, text in (
        ("docs/versions.md", versions_doc),
        ("docs/reproducibility/version-matrix.md", matrix_doc),
    ):
        if version not in text:
            errors.append(f"{path} does not identify release {version}")
    if "make version-check" not in policy_doc:
        errors.append("dependency policy does not document make version-check")

    runtime = _requirements(root / "backend/requirements.txt", errors)
    development = _requirements(root / "backend/requirements-dev.txt", errors)
    constraints = _requirements(root / "backend/constraints.txt", errors)
    for name, pinned_version in {**runtime, **development}.items():
        if constraints.get(name) != pinned_version:
            errors.append(
                f"backend/constraints.txt has {name}=={constraints.get(name)!s}, expected {pinned_version}"
            )

    makefile = _read(root / "Makefile", errors)
    if "frontend-install:\n\tcd frontend && npm ci" not in makefile:
        errors.append("frontend-install must use npm ci")
    if re.search(r"\bnpm\s+install\b", makefile):
        errors.append("Makefile contains mutable npm install usage")
    if "--constraint backend/constraints.txt" not in makefile:
        errors.append("backend-install must consume backend/constraints.txt")
    if "version-check:" not in makefile:
        errors.append("Makefile is missing version-check")

    dockerfiles = _dockerfiles(root)
    docker_digests: set[str] = set()
    commit_values: dict[str, set[str]] = {}
    mutable_patterns = (
        re.compile(r"/latest/", re.IGNORECASE),
        re.compile(r":latest(?:\s|$|['\"])", re.IGNORECASE),
        re.compile(r"\bREL=(?:latest|LTS)\b", re.IGNORECASE),
    )
    for dockerfile in dockerfiles:
        rel = dockerfile.relative_to(root)
        text = _read(dockerfile, errors)
        for pattern in mutable_patterns:
            if pattern.search(text):
                errors.append(f"{rel}: mutable latest reference is forbidden")
        if re.search(r"^ARG\s+[A-Z0-9_]+_COMMIT=\s*$", text, re.MULTILINE):
            errors.append(f"{rel}: empty commit build argument")
        arg_defaults = dict(re.findall(r"^ARG\s+([A-Za-z_][A-Za-z0-9_]*)=(\S+)\s*$", text, re.MULTILINE))
        for number, line in enumerate(text.splitlines(), 1):
            match = re.match(r"\s*FROM(?:\s+--platform=\S+)?\s+(\S+)", line)
            if not match:
                continue
            image = match.group(1)
            variable = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", image)
            resolved = arg_defaults.get(variable.group(1), "") if variable else image
            digest = SHA256.search(resolved)
            if not digest or digest.end() != len(resolved):
                errors.append(f"{rel}:{number}: FROM input is not pinned by a full sha256 digest")
            else:
                docker_digests.add(digest.group())
        if "runtime" not in rel.parts:
            if f"ARG LAIN5G_VERSION={version}" not in text:
                errors.append(f"{rel}: LAIN5G_VERSION does not match VERSION")
            if 'org.opencontainers.image.version="${LAIN5G_VERSION}"' not in text:
                errors.append(f"{rel}: missing synchronized OCI version label")

    for rel_name, arguments in SOURCE_COMMITS.items():
        text = _read(root / rel_name, errors)
        for argument in arguments:
            match = re.search(rf"^ARG {re.escape(argument)}=([^\s]+)$", text, re.MULTILINE)
            value = match.group(1) if match else ""
            if not GIT_COMMIT.fullmatch(value):
                errors.append(f"{rel_name}: {argument} must default to a full Git commit")
                continue
            commit_values.setdefault(argument, set()).add(value)
            if value not in matrix_doc:
                errors.append(f"version matrix omits {argument}={value}")
            if f'"${{{argument}}}"' not in text or "rev-parse" not in text:
                errors.append(f"{rel_name}: {argument} is not checked during the build")
    for argument, values in commit_values.items():
        if len(values) > 1:
            errors.append(f"Dockerfiles contradict each other for {argument}: {sorted(values)}")

    for digest in sorted(docker_digests):
        if digest not in matrix_doc:
            errors.append(f"version matrix omits Docker base digest {digest}")

    compose_files = _compose_files(root)
    for compose in compose_files:
        rel = compose.relative_to(root)
        text = _read(compose, errors)
        for pattern in mutable_patterns:
            if pattern.search(text):
                errors.append(f"{rel}: mutable latest reference is forbidden")
        for number, line in enumerate(text.splitlines(), 1):
            match = re.match(r"\s*image:\s*['\"]?([^'\"\s]+)", line)
            if not match:
                continue
            image = match.group(1)
            if image.startswith(("lain5g-lab/", "lain5g/")):
                if "deployments/ims-real" in rel.as_posix() and not image.endswith(f":{version}"):
                    errors.append(f"{rel}:{number}: derived image tag {image!r} != release {version}")
                continue
            digest = SHA256.search(image)
            if not digest or digest.end() != len(image):
                errors.append(f"{rel}:{number}: third-party image {image!r} is not digest-pinned")

    catalog = _read(root / "backend/app/services/image_catalog.py", errors)
    for source in re.findall(r'"lain5g-lab/[^\"]+:local": \("([^\"]+)"', catalog):
        digest = SHA256.search(source)
        if not digest or digest.end() != len(source):
            errors.append(f"image catalog source {source!r} is not digest-pinned")
    for pattern in mutable_patterns:
        if pattern.search(catalog):
            errors.append("backend image catalog contains a mutable latest reference")

    ims_lock = _read(root / "deployments/ims-real/images.lock.yaml", errors)
    if f"release_version: {version}" not in ims_lock:
        errors.append("real-IMS image lock release_version contradicts VERSION")
    derived = re.findall(r"^\s+-\s+(lain5g-lab/\S+)\s*$", ims_lock, re.MULTILINE)
    if not derived or any(not image.endswith(f":{version}") for image in derived):
        errors.append("real-IMS derived image tags do not all match VERSION")
    for pattern in mutable_patterns:
        if pattern.search(ims_lock):
            errors.append("real-IMS image lock contains a mutable latest reference")

    service = _read(root / "backend/app/services/real_ims_service.py", errors)
    if "from ..version import VERSION" not in service or ':{VERSION}' not in service:
        errors.append("real-IMS service image tags must derive from VERSION")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Lain5G-Lab release and dependency consistency")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    errors = check(args.root)
    if errors:
        print(f"version-check: FAIL ({len(errors)} contradiction(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    version = (args.root / "VERSION").read_text(encoding="utf-8").strip()
    print(f"version-check: OK ({version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
