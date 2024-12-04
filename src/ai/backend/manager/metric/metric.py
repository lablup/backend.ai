import asyncio
import time

from prometheus_client import Counter, Gauge, Histogram, generate_latest


class APIMetrics:
    _request_count: Counter
    _request_duration: Histogram

    def __init__(self) -> None:
        self._request_count = Counter(
            name="backendai_api_request_count",
            documentation="Total number of API requests",
            labelnames=["method", "endpoint", "status_code"],
        )
        self._request_duration = Histogram(
            name="backendai_api_request_duration_sec",
            documentation="Duration of API requests in milliseconds",
            labelnames=["method", "endpoint", "status_code"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10],
        )

    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def _update_request_total(self, *, method: str, endpoint: str, status_code: int):
        self._request_count.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

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
    _event_count: Counter
    _event_failure_count: Counter
    _event_processing_time: Histogram

    def __init__(self) -> None:
        self._event_count = Counter(
            name="backendai_event_count",
            documentation="Total number of events processed",
            labelnames=["event_type"],
        )
        self._event_failure_count = Counter(
            name="backendai_event_failure_count",
            documentation="Number of failed events",
            labelnames=["event_type"],
        )
        self._event_processing_time = Histogram(
            name="backendai_event_processing_time_sec",
            documentation="Processing time of events in seconds",
            labelnames=["event_type", "status"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10],
        )

    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def update_success_event_metric(self, *, event_type: str, duration: float) -> None:
        self._event_count.labels(event_type=event_type).inc()
        self._event_processing_time.labels(event_type=event_type, status="success").observe(
            duration
        )

    def update_failure_event_metric(self, *, event_type: str, duration: float) -> None:
        self._event_failure_count.labels(event_type=event_type).inc()
        self._event_count.labels(event_type=event_type).inc()
        self._event_processing_time.labels(event_type=event_type, status="failure").observe(
            duration
        )


class BgTaskMetrics:
    _bgtask_count: Gauge
    _bgtask_done_count: Counter
    _bgtask_processing_time: Histogram

    def __init__(self) -> None:
        self._bgtask_count = Gauge(
            name="backendai_bgtask_count",
            documentation="Total number of background tasks processed",
            labelnames=["task_name"],
        )
        self._bgtask_done_count = Counter(
            name="backendai_bgtask_done_count",
            documentation="Number of completed background tasks",
            labelnames=["task_name", "status"],
        )
        self._bgtask_processing_time = Histogram(
            name="backendai_bgtask_processing_time_sec",
            documentation="Processing time of background tasks in seconds",
            labelnames=["task_name", "status"],
            buckets=[0.1, 1, 10, 30, 60, 300, 600],
        )

    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def bgtask_started(self, *, task_name: str) -> None:
        self._bgtask_count.labels(task_name=task_name).inc()

    def bgtask_done(self, *, task_name: str, status: str, duration: float) -> None:
        self._bgtask_count.labels(task_name=task_name).dec()
        self._bgtask_processing_time.labels(task_name=task_name, status=status).observe(duration)
        self._bgtask_done_count.labels(task_name=task_name, status=status).inc()


class CommonMetric:
    _up: Gauge
    _up_time: Gauge
    _coroutines: Gauge
    _boot_time: float

    def __init__(self) -> None:
        self._up = Gauge(
            name="backendai_up",
            documentation="BackendAI service is up",
        )
        self._coroutines = Gauge(
            name="backendai_coroutines",
            documentation="Total number of coroutines running",
        )
        self._boot_time = time.time()
        self._up.set(1)
        self._up_time = Gauge(
            name="backendai_up_time",
            documentation="BackendAI service is up time",
        )

    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def _update_coroutines(self) -> None:
        count = len(asyncio.all_tasks())
        self._coroutines.set(count)

    def update(self) -> None:
        self._update_coroutines()
        self._up_time.set(time.time() - self._boot_time)


class MetricRegistry:
    api: APIMetrics
    event: EventMetrics
    bgtask: BgTaskMetrics
    common: CommonMetric

    def __init__(self) -> None:
        self.api = APIMetrics.instance()
        self.event = EventMetrics.instance()
        self.bgtask = BgTaskMetrics.instance()
        self.common = CommonMetric.instance()

    def to_prometheus(self) -> bytes:
        self.common.update()
        return generate_latest()
