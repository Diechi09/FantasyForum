from collections import Counter, defaultdict
import threading


class MetricsRegistry:
    """Thread-safe container for lightweight application metrics."""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests_by_endpoint = Counter()
        self._responses_by_status = Counter()
        self._latency_totals = defaultdict(float)
        self._latency_counts = Counter()

    def record_request(self, endpoint: str, status_code: int, elapsed_seconds: float) -> None:
        with self._lock:
            self._requests_by_endpoint[endpoint] += 1
            self._responses_by_status[str(status_code)] += 1
            self._latency_totals[endpoint] += elapsed_seconds
            self._latency_counts[endpoint] += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "requests_by_endpoint": dict(self._requests_by_endpoint),
                "responses_by_status": dict(self._responses_by_status),
                "average_latency_seconds": {
                    endpoint: self._latency_totals[endpoint] / self._latency_counts[endpoint]
                    for endpoint in self._latency_counts
                },
            }
