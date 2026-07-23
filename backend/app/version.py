from __future__ import annotations

import re
from pathlib import Path


VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"
VERSION = VERSION_FILE.read_text(encoding="utf-8").strip()

if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", VERSION):
    raise RuntimeError(f"Invalid release version in {VERSION_FILE}")
