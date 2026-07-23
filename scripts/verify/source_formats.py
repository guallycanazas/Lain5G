#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import yaml

from _common import ROOT, relative, source_files


EXPECTED_INVALID_JSON = {
    "backend/tests/fixtures/runs/run-invalid/metadata.json",
}
PYTHON_ENTRYPOINTS = {"lain5g"}


def _line(error: BaseException) -> int | None:
    mark = getattr(error, "problem_mark", None)
    return mark.line + 1 if mark is not None else getattr(error, "lineno", None)


def main() -> int:
    errors: list[str] = []
    counts = {"Python": 0, "Shell": 0, "YAML": 0, "JSON": 0}
    files = source_files()
    relative_files = {relative(path) for path in files}

    missing_exclusions = EXPECTED_INVALID_JSON - relative_files
    if missing_exclusions:
        errors.extend(f"expected-invalid fixture is missing: {path}" for path in sorted(missing_exclusions))

    for path in files:
        rel = relative(path)
        suffix = path.suffix.lower()

        if suffix == ".py" or rel in PYTHON_ENTRYPOINTS:
            counts["Python"] += 1
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=rel)
            except (OSError, UnicodeError, SyntaxError) as exc:
                location = f":{_line(exc)}" if _line(exc) is not None else ""
                errors.append(f"{rel}{location}: invalid Python syntax ({type(exc).__name__})")

        if suffix in {".sh", ".bash"}:
            counts["Shell"] += 1
            result = subprocess.run(
                ["bash", "-n", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if result.returncode != 0:
                errors.append(f"{rel}: invalid shell syntax")

        if suffix in {".yaml", ".yml"}:
            counts["YAML"] += 1
            try:
                with path.open(encoding="utf-8") as stream:
                    list(yaml.safe_load_all(stream))
            except (OSError, UnicodeError, yaml.YAMLError) as exc:
                location = f":{_line(exc)}" if _line(exc) is not None else ""
                errors.append(f"{rel}{location}: invalid YAML ({type(exc).__name__})")

        if suffix == ".json" and rel not in EXPECTED_INVALID_JSON:
            counts["JSON"] += 1
            try:
                with path.open(encoding="utf-8") as stream:
                    json.load(stream)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                location = f":{_line(exc)}" if _line(exc) is not None else ""
                errors.append(f"{rel}{location}: invalid JSON ({type(exc).__name__})")

    if errors:
        print(f"source-formats: FAIL ({len(errors)} error(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    summary = ", ".join(f"{name}={count}" for name, count in counts.items())
    excluded = ", ".join(sorted(EXPECTED_INVALID_JSON))
    print(f"source-formats: OK ({summary}; expected-invalid JSON excluded: {excluded})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
