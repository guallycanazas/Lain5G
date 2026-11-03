from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_metrics_endpoint_reports_build_and_bounded_http_labels() -> None:
    with TestClient(create_app()) as client:
        health = client.get("/api/health")
        metrics = client.get("/metrics")

    assert health.status_code == 200
    assert metrics.status_code == 200
    assert "text/plain" in metrics.headers["content-type"]
    body = metrics.text
    assert "openlain5g_backend_build_info" in body
    assert 'handler="/api/health"' in body
    assert 'method="GET"' in body
    assert 'status="200"' in body
    assert 'handler="/metrics"' not in body
