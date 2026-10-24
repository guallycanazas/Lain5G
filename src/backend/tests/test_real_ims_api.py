import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app

ROOT = Path(__file__).resolve().parents[3]


def test_real_ims_routes_are_available_through_local_api():
    with TestClient(create_app()) as client:
        paths = client.get("/openapi.json").json()["paths"]
        response = client.get("/api/ims-real/status?mode=4g")

    assert "/api/ims-real/preflight" in paths
    assert "/api/ims-real/status" in paths
    assert "/api/ims-real/subscribers" in paths
    assert "/api/ims-real/sync-subscriber" in paths
    assert response.status_code == 200


def test_internal_signaling_has_no_public_cli_entrypoint():
    assert not (ROOT / "scripts/ims_real.py").exists()
    for target in ("start-4g-volte-sim", "start-5g-vonr-sim", "ims-real-status"):
        result = subprocess.run(["make", target], cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode != 0
        assert "not part of the public operational interface" in result.stderr
