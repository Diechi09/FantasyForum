"""Monitoring utilities for the Flask application."""

import os
import time
from typing import List, Optional

from flask import Response, request

try:  # pragma: no cover - dependency provided in production
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ImportError:  # pragma: no cover - lightweight fallback for offline environments
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    _FALLBACK_METRICS: List["_BaseMetric"] = []

    class _BaseMetric:
        def __init__(self, name, documentation, labelnames):
            self._name = name
            self._documentation = documentation
            self._labelnames = labelnames
            _FALLBACK_METRICS.append(self)

        def labels(self, **kwargs):
            return self

    class Counter(_BaseMetric):
        _type = "counter"

        def inc(self, amount=1):
            return self

    class Histogram(_BaseMetric):
        _type = "histogram"

        def observe(self, amount):
            return self

    def generate_latest():
        lines = []
        for metric in _FALLBACK_METRICS:
            lines.append(f"# HELP {metric._name} {metric._documentation}")
            lines.append(f"# TYPE {metric._name} {metric._type}")
            lines.append(f"{metric._name} 0")
        return "\n".join(lines).encode()


REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)
ERROR_COUNTER = Counter(
    "http_request_errors_total",
    "HTTP requests resulting in errors (status >= 500)",
    ["endpoint"],
)


def _get_endpoint_label() -> str:
    """Return a stable endpoint label for metrics."""

    return request.endpoint or request.path or "unknown"


def register_monitoring(app):
    """Register Prometheus monitoring middleware and endpoints."""

    @app.before_request
    def start_timer():  # noqa: WPS430
        request._start_time = time.perf_counter()  # noqa: WPS437

    @app.after_request
    def record_metrics(response):  # noqa: WPS430
        start_time: Optional[float] = getattr(request, "_start_time", None)
        if start_time is not None:
            latency = time.perf_counter() - start_time
        else:
            latency = 0

        endpoint_label = _get_endpoint_label()
        REQUEST_COUNTER.labels(
            method=request.method,
            endpoint=endpoint_label,
            status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint_label).observe(latency)
        if response.status_code >= 500:
            ERROR_COUNTER.labels(endpoint=endpoint_label).inc()

        return response

    @app.route("/metrics")
    def metrics():  # noqa: WPS430
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


def configure_application_insights(app):
    """Configure Azure Application Insights if connection string is provided."""

    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        return

    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.ext.flask.flask_middleware import FlaskMiddleware
    from opencensus.trace.samplers import ProbabilitySampler

    FlaskMiddleware(
        app,
        exporter=AzureExporter(connection_string=connection_string),
        sampler=ProbabilitySampler(1.0),
    )
