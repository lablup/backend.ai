from typing import Optional, Self

from prometheus_client import Counter, Gauge, Histogram

from .types import FlattenedDeviceMetric, FlattenedKernelMetric


class RPCMetricObserver:
    _instance: Optional[Self] = None

    _rpc_requests: Counter
    _rpc_failure_requests: Counter
    _rpc_request_duration: Histogram

    def __init__(self) -> None:
        self._rpc_requests = Counter(
            name="backendai_rpc_requests_total",
            documentation="Number of RPC requests",
            labelnames=["method"],
        )
        self._rpc_failure_requests = Counter(
            name="backendai_rpc_failure_requests_total",
            documentation="Number of failed RPC requests",
            labelnames=["method", "exception"],
        )
        self._rpc_request_duration = Histogram(
            name="backendai_rpc_request_duration_seconds",
            documentation="Duration of RPC requests",
            labelnames=["method"],
            buckets=[0.1, 1, 10, 30, 60, 300, 600],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_rpc_request_success(self, *, method: str, duration: float) -> None:
        self._rpc_requests.labels(method=method).inc()
        self._rpc_request_duration.labels(method=method).observe(duration)

    def observe_rpc_request_failure(
        self, *, method: str, duration: float, exception: BaseException
    ) -> None:
        exception_name = exception.__class__.__name__
        self._rpc_requests.labels(method=method).inc()
        self._rpc_failure_requests.labels(method=method, exception=exception_name).inc()
        self._rpc_request_duration.labels(method=method).observe(duration)


class UtilizationMetricObserver:
    _instance: Optional[Self] = None

    _container_metric: Gauge
    _device_metric: Gauge

    def __init__(self) -> None:
        self._container_metric = Gauge(
            name="backendai_container_utilization",
            documentation="Container utilization metrics",
            labelnames=["metric_name", "agent_id", "kernel_id", "value_type"],
        )
        self._device_metric = Gauge(
            name="backendai_device_utilization",
            documentation="Device utilization metrics",
            labelnames=["metric_name", "agent_id", "device_id", "value_type"],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_container_metric(
        self,
        *,
        metric: FlattenedKernelMetric,
    ) -> None:
        for metric_value_type, value in metric.value_pairs:
            self._container_metric.labels(
                metric_name=metric.key,
                agent_id=metric.agent_id,
                kernel_id=metric.kernel_id,
                value_type=metric_value_type,
            ).set(float(value))

    def observe_device_metric(
        self,
        *,
        metric: FlattenedDeviceMetric,
    ) -> None:
        for metric_value_type, value in metric.value_pairs:
            self._device_metric.labels(
                metric_name=metric.key,
                agent_id=metric.agent_id,
                device_id=metric.device_id,
                value_type=metric_value_type,
            ).set(float(value))
