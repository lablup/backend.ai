import asyncio
import enum
import functools
import uuid
from collections.abc import Iterable
from typing import Optional, Self

from prometheus_client import Counter, Gauge, Histogram

from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    DEVICE_UTILIZATION_METRIC_LABEL_NAME,
    UNDEFINED,
    UTILIZATION_METRIC_DETENTION,
)
from ai.backend.common.types import AgentId, KernelId, MetricKey, SessionId

from .types import (
    ALL_METRIC_VALUE_TYPES,
    FlattenedDeviceMetric,
    FlattenedKernelMetric,
)


class StatScope(enum.StrEnum):
    NODE = "node"
    CONTAINER = "container"
    PROCESS = "process"


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
    _removal_tasks: dict[KernelId, asyncio.Task[None]]

    _container_metric: Gauge
    _device_metric: Gauge

    def __init__(self) -> None:
        self._removal_tasks = {}
        self._container_metric = Gauge(
            name="backendai_container_utilization",
            documentation="Container utilization metrics",
            labelnames=[
                CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
                "agent_id",
                "kernel_id",
                "session_id",
                "user_id",
                "project_id",
                "value_type",
            ],
        )
        self._device_metric = Gauge(
            name="backendai_device_utilization",
            documentation="Device utilization metrics",
            labelnames=[
                DEVICE_UTILIZATION_METRIC_LABEL_NAME,
                "agent_id",
                "device_id",
                "value_type",
            ],
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
                container_metric_name=metric.key,
                agent_id=metric.agent_id,
                kernel_id=metric.kernel_id,
                session_id=metric.session_id or UNDEFINED,
                user_id=metric.owner_user_id or UNDEFINED,
                project_id=metric.project_id or UNDEFINED,
                value_type=metric_value_type,
            ).set(float(value))

    async def lazy_remove_container_metric(
        self,
        *,
        agent_id: AgentId,
        kernel_id: KernelId,
        session_id: Optional[SessionId],
        owner_user_id: Optional[uuid.UUID],
        project_id: Optional[uuid.UUID],
        keys: Iterable[MetricKey],
    ) -> None:
        async def remove_later() -> None:
            await asyncio.sleep(UTILIZATION_METRIC_DETENTION)
            for key in keys:
                for value_type in ALL_METRIC_VALUE_TYPES:
                    try:
                        self._container_metric.remove(
                            key,
                            agent_id,
                            kernel_id,
                            session_id or UNDEFINED,
                            owner_user_id or UNDEFINED,
                            project_id or UNDEFINED,
                            value_type,
                        )
                    except KeyError:
                        continue

        def callback(task: asyncio.Task) -> None:
            self._removal_tasks.pop(kernel_id, None)

        task = asyncio.create_task(remove_later())
        self._removal_tasks[kernel_id] = task
        task.add_done_callback(functools.partial(callback))

    def observe_device_metric(
        self,
        *,
        metric: FlattenedDeviceMetric,
    ) -> None:
        for metric_value_type, value in metric.value_pairs:
            self._device_metric.labels(
                device_metric_name=metric.key,
                agent_id=metric.agent_id,
                device_id=metric.device_id,
                value_type=metric_value_type,
            ).set(float(value))


class SyncContainerLifecycleObserver:
    _instance: Optional[Self] = None

    _task_trigger_count: Counter
    _task_success_count: Counter
    _task_failure_count: Counter

    def __init__(self) -> None:
        self._task_trigger_count = Counter(
            name="backendai_sync_container_lifecycle_trigger_count",
            documentation="Number of sync_container_lifecycle() task triggered",
            labelnames=["agent_id"],
        )
        self._task_success_count = Counter(
            name="backendai_sync_container_lifecycle_success_count",
            documentation="Number of sync_container_lifecycle() task succeeded",
            labelnames=["agent_id"],
        )
        self._task_failure_count = Counter(
            name="backendai_sync_container_lifecycle_failure_count",
            documentation="Number of sync_container_lifecycle() task failed",
            labelnames=["agent_id", "exception"],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_container_lifecycle_triggered(
        self,
        *,
        agent_id: AgentId,
    ) -> None:
        self._task_trigger_count.labels(agent_id=agent_id).inc()

    def observe_container_lifecycle_success(
        self,
        *,
        agent_id: AgentId,
        num_synced_kernels: int,
    ) -> None:
        self._task_success_count.labels(agent_id=agent_id).inc(amount=num_synced_kernels)

    def observe_container_lifecycle_failure(
        self,
        *,
        agent_id: AgentId,
        exception: BaseException,
    ) -> None:
        exception_name = exception.__class__.__name__
        self._task_failure_count.labels(agent_id=agent_id, exception=exception_name).inc()


class StatTaskObserver:
    _instance: Optional[Self] = None

    _task_trigger_count: Counter
    _task_success_count: Counter
    _task_failure_count: Counter

    def __init__(self) -> None:
        self._task_trigger_count = Counter(
            name="backendai_stat_task_trigger_count",
            documentation="Number of stat() task triggered",
            labelnames=["agent_id", "stat_scope"],
        )
        self._task_success_count = Counter(
            name="backendai_stat_task_success_count",
            documentation="Number of stat() task succeeded",
            labelnames=["agent_id", "stat_scope"],
        )
        self._task_failure_count = Counter(
            name="backendai_stat_task_failure_count",
            documentation="Number of stat() task failed",
            labelnames=["agent_id", "stat_scope", "exception"],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_stat_task_triggered(
        self,
        *,
        agent_id: AgentId,
        stat_scope: StatScope,
    ) -> None:
        self._task_trigger_count.labels(agent_id=agent_id, stat_scope=stat_scope).inc()

    def observe_stat_task_success(
        self,
        *,
        agent_id: AgentId,
        stat_scope: StatScope,
    ) -> None:
        self._task_success_count.labels(agent_id=agent_id, stat_scope=stat_scope).inc()

    def observe_stat_task_failure(
        self,
        *,
        agent_id: AgentId,
        stat_scope: StatScope,
        exception: BaseException,
    ) -> None:
        exception_name = exception.__class__.__name__
        self._task_failure_count.labels(
            agent_id=agent_id, stat_scope=stat_scope, exception=exception_name
        ).inc()
