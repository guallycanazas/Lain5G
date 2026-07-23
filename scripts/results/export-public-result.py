#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from public_result import MAX_INPUT_BYTES, ROOT, PublicResultError, export_public_result, load_json_bytes


def _read_input(path: str) -> bytes:
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        try:
            raw = Path(path).read_bytes()
        except OSError as exc:
            raise PublicResultError("input could not be read") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise PublicResultError("input exceeds the public summary size limit")
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a pre-sanitized summary as a deterministic public scenario result."
    )
    parser.add_argument("input", help="safe summary JSON path, or - for standard input")
    arguments = parser.parse_args()

    try:
        value = load_json_bytes(_read_input(arguments.input))
        target = export_public_result(value, root=ROOT)
    except PublicResultError as exc:
        print(f"public-result-export: FAIL ({exc})", file=sys.stderr)
        return 1

    print(f"public-result-export: OK ({target.relative_to(ROOT).as_posix()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
