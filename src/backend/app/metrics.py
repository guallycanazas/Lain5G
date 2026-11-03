from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    GCCollector,
    Gauge,
    Histogram,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
)

from .version import VERSION


def configure_metrics(app: FastAPI) -> None:
    """Expose bounded-cardinality HTTP and Python process metrics."""
    registry = CollectorRegistry()
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)
    GCCollector(registry=registry)

    requests = Counter(
        "openlain5g_http_requests_total",
        "HTTP requests served by the OpenLain5G backend.",
        ("method", "handler", "status"),
        registry=registry,
    )
    request_duration = Histogram(
        "openlain5g_http_request_duration_seconds",
        "HTTP request duration in seconds.",
        ("method", "handler"),
        registry=registry,
    )
    build_info = Gauge(
        "openlain5g_backend_build_info",
        "OpenLain5G backend version information.",
        ("version",),
        registry=registry,
    )
    build_info.labels(version=VERSION).set(1)

    @app.middleware("http")
    async def record_http_metrics(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        started = perf_counter()
        status = "500"
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        finally:
            route = request.scope.get("route")
            handler = getattr(route, "path", "unmatched")
            requests.labels(method=request.method, handler=handler, status=status).inc()
            request_duration.labels(method=request.method, handler=handler).observe(perf_counter() - started)

    async def metrics_endpoint() -> Response:
        return Response(content=generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})

    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)
