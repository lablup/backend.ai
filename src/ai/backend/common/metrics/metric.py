import asyncio
import os
from typing import Optional, Self

import psutil
from prometheus_client import Counter, Gauge, Histogram, generate_latest


class APIMetricObserver:
    _instance: Optional[Self] = None

    _request_count: Counter
    _request_duration_sec: Histogram

    def __init__(self) -> None:
        self._request_count = Counter(
            name="backendai_api_request_count",
            documentation="Total number of API requests",
            labelnames=["method", "endpoint", "status_code"],
        )
        self._request_duration_sec = Histogram(
            name="backendai_api_request_duration_sec",
            documentation="Duration of API requests in milliseconds",
            labelnames=["method", "endpoint", "status_code"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _inc_request_total(self, *, method: str, endpoint: str, status_code: int) -> None:
        self._request_count.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    def _observe_request_duration(
        self, *, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        self._request_duration_sec.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration)

    def observe_request(
        self, *, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        self._inc_request_total(method=method, endpoint=endpoint, status_code=status_code)
        self._observe_request_duration(
            method=method, endpoint=endpoint, status_code=status_code, duration=duration
        )


class EventMetricObserver:
    _instance: Optional[Self] = None

    _event_count: Counter
    _event_failure_count: Counter
    _event_processing_time_sec: Histogram

    def __init__(self) -> None:
        self._event_count = Counter(
            name="backendai_event_count",
            documentation="Total number of events processed",
            labelnames=["event_type"],
        )
        self._event_failure_count = Counter(
            name="backendai_event_failure_count",
            documentation="Number of failed events",
            labelnames=["event_type", "exception"],
        )
        self._event_processing_time_sec = Histogram(
            name="backendai_event_processing_time_sec",
            documentation="Processing time of events in seconds",
            labelnames=["event_type", "status"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_event_success(self, *, event_type: str, duration: float) -> None:
        self._event_count.labels(event_type=event_type).inc()
        self._event_processing_time_sec.labels(event_type=event_type, status="success").observe(
            duration
        )

    def observe_event_failure(
        self, *, event_type: str, duration: float, exception: Exception
    ) -> None:
        exception_name = exception.__class__.__name__
        self._event_failure_count.labels(event_type=event_type, exeception=exception_name).inc()
        self._event_count.labels(event_type=event_type).inc()
        self._event_processing_time_sec.labels(event_type=event_type, status="failure").observe(
            duration
        )


class BgTaskMetricObserver:
    _instance: Optional[Self] = None

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
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_bgtask_started(self, *, task_name: str) -> None:
        self._bgtask_count.labels(task_name=task_name).inc()

    def observe_bgtask_done(self, *, task_name: str, status: str, duration: float) -> None:
        self._bgtask_count.labels(task_name=task_name).dec()
        self._bgtask_processing_time.labels(task_name=task_name, status=status).observe(duration)
        self._bgtask_done_count.labels(task_name=task_name, status=status).inc()


class SystemMetricObserver:
    _instance: Optional[Self] = None

    _async_task_count: Gauge
    _cpu_usage_percent: Gauge
    _memory_used_rss: Gauge
    _memory_used_vms: Gauge

    def __init__(self) -> None:
        self._async_task_count = Gauge(
            name="backendai_async_task_count",
            documentation="Number of active async tasks",
        )
        self._cpu_usage_percent = Gauge(
            name="backendai_cpu_usage_percent",
            documentation="CPU usage of the process",
        )
        self._memory_used_rss = Gauge(
            name="backendai_memory_used_rss",
            documentation="Memory used by the process in RSS",
        )
        self._memory_used_vms = Gauge(
            name="backendai_memory_used_vms",
            documentation="Memory used by the process in VMS",
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe(self) -> None:
        self._async_task_count.set(len(asyncio.all_tasks()))
        proc = psutil.Process(os.getpid())
        self._cpu_usage_percent.set(proc.cpu_percent())
        self._memory_used_rss.set(proc.memory_info().rss)
        self._memory_used_vms.set(proc.memory_info().vms)


class CommonMetricRegistry:
    _instance: Optional[Self] = None

    api: APIMetricObserver
    event: EventMetricObserver
    bgtask: BgTaskMetricObserver
    system: SystemMetricObserver

    def __init__(self) -> None:
        self.api = APIMetricObserver.instance()
        self.event = EventMetricObserver.instance()
        self.bgtask = BgTaskMetricObserver.instance()
        self.system = SystemMetricObserver.instance()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def to_prometheus(self) -> str:
        self.system.observe()
        return generate_latest().decode("utf-8")
