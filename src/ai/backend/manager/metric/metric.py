from prometheus_client import Counter, Histogram, generate_latest


class APIMetrics:
    _request_total: Counter
    _request_duration: Histogram

    def __init__(self) -> None:
        self._request_total = Counter(
            name="backendai_api_requests_total",
            documentation="Total number of API requests",
            labelnames=["method", "endpoint", "status_code"],
        )
        self._request_duration = Histogram(
            name="backendai_api_request_duration_ms",
            documentation="Duration of API requests in milliseconds",
            labelnames=["method", "endpoint", "status_code"],
            buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000, 10000],
        )

    def _update_request_total(self, *, method: str, endpoint: str, status_code: int):
        self._request_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    def _update_request_duration(
        self, *, method: str, endpoint: str, status_code: int, duration: float
    ):
        self._request_duration.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).observe(duration)

    def update_request_metric(
        self, *, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        self._update_request_total(method=method, endpoint=endpoint, status_code=status_code)
        self._update_request_duration(
            method=method, endpoint=endpoint, status_code=status_code, duration=duration
        )


class EventMetrics:
    _event_total: Counter
    _event_failure_count: Counter
    _event_processing_time: Histogram

    def __init__(self) -> None:
        self._event_total = Counter(
            name="backendai_event_total",
            documentation="Total number of events processed",
            labelnames=["event_type"],
        )
        self._event_failure_count = Counter(
            name="backendai_event_failure_count",
            documentation="Number of failed events",
            labelnames=["event_type"],
        )
        self._event_processing_time = Histogram(
            name="backendai_event_processing_time",
            documentation="Processing time of events in seconds",
            labelnames=["event_type", "status"],
        )

    def update_success_event_metric(self, *, event_type: str, duration: float) -> None:
        self._event_total.labels(event_type=event_type).inc()
        self._event_processing_time.labels(event_type=event_type, status="success").observe(
            duration
        )

    def update_failure_event_metric(self, *, event_type: str, duration: float) -> None:
        self._event_failure_count.labels(event_type=event_type).inc()
        self._event_total.labels(event_type=event_type).inc()
        self._event_processing_time.labels(event_type=event_type, status="failure").observe(
            duration
        )


class MetricRegistry:
    api: APIMetrics
    event: EventMetrics

    def __init__(self) -> None:
        self.api = APIMetrics()
        self.event = EventMetrics()

    def to_prometheus(self) -> bytes:
        return generate_latest()
