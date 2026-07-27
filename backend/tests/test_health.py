from pathlib import Path


def test_health_responds_ok(client):
    version = (Path(__file__).resolve().parents[2] / "VERSION").read_text(encoding="utf-8").strip()
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "lain5g-lab-backend",
        "version": version,
        "dry_run": True,
    }
