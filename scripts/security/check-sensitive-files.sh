#!/usr/bin/env bash

set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null) || {
    printf '%s\n' '{"category":"scanner","path":".","approx_line":0,"severity":"high","result":"ERROR"}'
    exit 2
}

if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' '{"category":"scanner","path":".","approx_line":0,"severity":"high","result":"ERROR"}'
    exit 2
fi

exec python3 - "$root" 2>/dev/null <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


root = Path(sys.argv[1])
proc = subprocess.run(
    [
        "git", "-C", os.fspath(root), "ls-files", "--cached", "--others",
        "--exclude-standard", "-z", "--",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    check=False,
)
if proc.returncode != 0:
    print(json.dumps({
        "category": "scanner",
        "path": ".",
        "approx_line": 0,
        "severity": "high",
        "result": "ERROR",
    }, separators=(",", ":")))
    raise SystemExit(2)

checks = {
    "private-key-material": 0,
    "provider-token": 0,
    "sensitive-filename": 0,
    "sensitive-artifact": 0,
}
private_key = re.compile(
    rb"-----BEGIN (?:RSA |DSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
)
provider_tokens = (
    re.compile(rb"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
    re.compile(rb"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,}(?![A-Za-z0-9])"),
    re.compile(rb"(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{20,}(?![A-Za-z0-9])"),
)
sensitive_suffixes = {
    ".key", ".pem", ".p12", ".pfx", ".jks", ".keystore", ".kdbx",
}
artifact_suffixes = {
    ".db", ".db3", ".sqlite", ".sqlite3", ".dump", ".bson", ".pcap", ".pcapng",
}
ssh_names = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
secret_stems = {"credential", "credentials", "secret", "secrets", "token", "tokens"}


def emit(category: str, path: str, line: int, severity: str, result: str) -> None:
    print(json.dumps({
        "category": category,
        "path": path,
        "approx_line": line,
        "severity": severity,
        "result": result,
    }, separators=(",", ":")))


def reviewed_example(path: PurePosixPath) -> bool:
    name = path.name.lower()
    return any(marker in name for marker in (".example.", ".sample.", ".template.")) or name.endswith(
        (".example", ".sample", ".template")
    )


for raw_path in proc.stdout.split(b"\0"):
    if not raw_path:
        continue
    relative = os.fsdecode(raw_path)
    posix_path = PurePosixPath(relative)
    target = root / relative
    if not target.is_file() or target.is_symlink():
        continue

    lower_name = posix_path.name.lower()
    suffix = posix_path.suffix.lower()
    if not reviewed_example(posix_path):
        category = None
        if suffix in sensitive_suffixes or lower_name in ssh_names:
            category = "sensitive-filename"
        elif (
            lower_name == ".env"
            or lower_name.startswith(".env.")
            or posix_path.stem.lower() in secret_stems
        ):
            category = "sensitive-filename"
        elif suffix in artifact_suffixes:
            category = "sensitive-artifact"
        if category:
            checks[category] += 1
            emit(category, relative, 1, "high", "FAIL")

    try:
        with target.open("rb") as stream:
            for line_number, line in enumerate(stream, start=1):
                if private_key.search(line):
                    checks["private-key-material"] += 1
                    emit("private-key-material", relative, line_number, "critical", "FAIL")
                if any(pattern.search(line) for pattern in provider_tokens):
                    checks["provider-token"] += 1
                    emit("provider-token", relative, line_number, "critical", "FAIL")
    except OSError:
        emit("scanner", relative, 0, "high", "ERROR")
        raise SystemExit(2)

for category, count in checks.items():
    if count == 0:
        severity = "critical" if category in {"private-key-material", "provider-token"} else "high"
        emit(category, ".", 0, severity, "PASS")

raise SystemExit(1 if any(checks.values()) else 0)
PY
