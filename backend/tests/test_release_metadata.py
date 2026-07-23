from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts" / "release" / "check-version.py"


def test_root_version_drives_api_and_health(client):
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    assert client.app.version == version
    assert client.get("/api/health").json()["version"] == version


def test_release_version_and_dependency_policy_passes():
    result = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "version-check: OK (1.0.0-rc.1)" in result.stdout


def test_release_policy_rejects_a_frontend_version_contradiction(tmp_path: Path):
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (tmp_path / "VERSION").write_text("1.0.0-rc.1\n", encoding="utf-8")
    (frontend / "package.json").write_text(
        json.dumps({"version": "9.9.9", "dependencies": {}, "devDependencies": {}}),
        encoding="utf-8",
    )
    (frontend / "package-lock.json").write_text(
        json.dumps({"version": "9.9.9", "packages": {"": {"version": "9.9.9"}}}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CHECK), "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "frontend/package.json version '9.9.9' != '1.0.0-rc.1'" in result.stderr
