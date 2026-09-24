from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
)

registry = CollectorRegistry()

requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "route", "status"],
    registry=registry,
)

active_requests = Gauge(
    "http_requests_active",
    "Number of currently active HTTP requests",
    registry=registry,
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route", "status"],
    buckets=[
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.0,
    ],
    registry=registry,
)
