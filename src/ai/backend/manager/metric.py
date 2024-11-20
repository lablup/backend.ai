from prometheus_client import Counter, Histogram, generate_latest


class APIMetrics:
    _request_total: Counter
    _request_duration: Histogram

    def __init__(self) -> None:
        self._request_total = Counter(
            name="backendai_api_requests_total",
            documentation="Total number of API requests",
            labelnames=["method", "endpoint", "status"],
        )
        self._request_duration = Histogram(
            name="backendai_api_request_duration_ms",
            documentation="Duration of API requests in milliseconds",
            labelnames=["method", "endpoint", "status"],
            buckets=[0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30],
        )

    def request_total(self, *, method: str, endpoint: str, status: str) -> Counter:
        return self._request_total.labels(method=method, endpoint=endpoint, status=status)

    def request_duration(self, *, method: str, endpoint: str, status: str) -> Histogram:
        return self._request_duration.labels(method=method, endpoint=endpoint, status=status)


class ComponentMetrics:
    _agent_status: Counter
    _agent_startup_time: Histogram
    _sessions_total: Counter
    _session_startup_time: Histogram
    _kernels_total: Counter
    _kernel_startup_time: Histogram
    _tasks_total: Counter
    _task_startup_time: Histogram

    def __init__(self) -> None:
        self._agent_status = Counter(
            name="backendai_agent_status",
            documentation="Status of the agent",
            labelnames=["status"],
        )
        self._agent_startup_time = Histogram(
            name="backendai_agent_startup_time",
            documentation="Startup time of the agent in seconds",
            labelnames=["agent_id"],
        )
        self._sessions_total = Counter(
            name="backendai_sessions_total",
            documentation="Total number of sessions",
            labelnames=["status"],
        )
        self._session_startup_time = Histogram(
            name="backendai_session_startup_time",
            documentation="Startup time of sessions in seconds",
            labelnames=["session_id"],
        )
        self._kernels_total = Counter(
            name="backendai_kernels_total",
            documentation="Total number of kernels",
            labelnames=["status"],
        )
        self._kernel_startup_time = Histogram(
            name="backendai_kernel_startup_time",
            documentation="Startup time of kernels in seconds",
            labelnames=["kernel_id"],
        )
        self._tasks_total = Counter(
            name="backendai_tasks_total",
            documentation="Total number of tasks",
            labelnames=["task_type", "status"],
        )
        self._task_startup_time = Histogram(
            name="backendai_task_startup_time",
            documentation="Startup time of tasks in seconds",
            labelnames=["task_type", "task_id"],
        )

    def agent_status(self, *, status: str) -> Counter:
        return self._agent_status.labels(status=status)

    def agent_startup_time(self, *, agent_id: str) -> Histogram:
        return self._agent_startup_time.labels(agent_id=agent_id)

    def sessions_total(self, *, status: str) -> Counter:
        return self._sessions_total.labels(status=status)

    def session_startup_time(self, *, session_id: str) -> Histogram:
        return self._session_startup_time.labels(session_id=session_id)

    def kernels_total(self, *, status: str) -> Counter:
        return self._kernels_total.labels(status=status)

    def kernel_startup_time(self, *, kernel_id: str) -> Histogram:
        return self._kernel_startup_time.labels(kernel_id=kernel_id)

    def tasks_total(self, *, task_type: str, status: str) -> Counter:
        return self._tasks_total.labels(task_type=task_type, status=status)

    def task_startup_time(self, *, task_type: str, task_id: str) -> Histogram:
        return self._task_startup_time.labels(task_type=task_type, task_id=task_id)


class CommonMetrics:
    _events_total: Counter
    _errors_total: Counter

    def __init__(self) -> None:
        self._events_total = Counter(
            name="backendai_events_total",
            documentation="Total number of events",
            labelnames=["event"],
        )
        self._errors_total = Counter(
            name="backendai_errors_total",
            documentation="Total number of errors",
            labelnames=["error_type"],
        )

    def events_total(self, *, event: str) -> Counter:
        return self._events_total.labels(event=event)

    def errors_total(self, *, error_type: str) -> Counter:
        return self._errors_total.labels(error_type=error_type)


class SchedulerMetrics:
    _schedule_attempts_total: Counter
    _schedule_failures_total: Counter
    _schedule_retries_total: Counter

    def __init__(self) -> None:
        self._schedule_attempts_total = Counter(
            name="backendai_scheduler_schedule_attempts_total",
            documentation="Total number of schedule attempts",
            labelnames=["status"],
        )
        self._schedule_failures_total = Counter(
            name="backendai_scheduler_schedule_failures_total",
            documentation="Total number of schedule failures",
            labelnames=["reason"],
        )
        self._schedule_retries_total = Counter(
            name="backendai_scheduler_schedule_retries_total",
            documentation="Total number of schedule retries",
        )

    def schedule_attempts_total(self, *, status: str) -> Counter:
        return self._schedule_attempts_total.labels(status=status)

    def schedule_failures_total(self, *, reason: str) -> Counter:
        return self._schedule_failures_total.labels(reason=reason)

    def schedule_retries_total(self) -> Counter:
        return self._schedule_retries_total


class MetricRegistry:
    api: APIMetrics
    component: ComponentMetrics
    common: CommonMetrics
    scheduler: SchedulerMetrics

    def __init__(self) -> None:
        self.api = APIMetrics()
        self.component = ComponentMetrics()
        self.common = CommonMetrics()
        self.scheduler = SchedulerMetrics()

    def to_prometheus(self) -> bytes:
        return generate_latest()
