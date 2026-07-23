def test_health_responds_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "lain5g-lab-backend",
        "version": "1.0.0-rc.1",
        "dry_run": True,
    }
