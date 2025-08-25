import asyncio
import enum
import os
from typing import Optional, Self

import psutil
from prometheus_client import Counter, Gauge, Histogram, generate_latest

from ai.backend.common.exception import BackendAIError, ErrorCode


class APIMetricObserver:
    _instance: Optional[Self] = None

    _request_count: Counter
    _request_duration_sec: Histogram

    def __init__(self) -> None:
        self._request_count = Counter(
            name="backendai_api_request_count",
            documentation="Total number of API requests",
            labelnames=["method", "endpoint", "domain", "operation", "error_detail", "status_code"],
        )
        self._request_duration_sec = Histogram(
            name="backendai_api_request_duration_sec",
            documentation="Duration of API requests in milliseconds",
            labelnames=["method", "endpoint", "domain", "operation", "error_detail", "status_code"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _inc_request_total(
        self, *, method: str, endpoint: str, error_code: Optional[ErrorCode], status_code: int
    ) -> None:
        self._request_count.labels(
            method=method,
            endpoint=endpoint,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
            status_code=status_code,
        ).inc()

    def _observe_request_duration(
        self,
        *,
        method: str,
        endpoint: str,
        error_code: Optional[ErrorCode],
        status_code: int,
        duration: float,
    ) -> None:
        self._request_duration_sec.labels(
            method=method,
            endpoint=endpoint,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
            status_code=status_code,
        ).observe(duration)

    def observe_request(
        self,
        *,
        method: str,
        endpoint: str,
        error_code: Optional[ErrorCode],
        status_code: int,
        duration: float,
    ) -> None:
        self._inc_request_total(
            method=method, endpoint=endpoint, error_code=error_code, status_code=status_code
        )
        self._observe_request_duration(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            error_code=error_code,
            duration=duration,
        )


class GraphQLMetricObserver:
    _instance: Optional[Self] = None

    _request_count: Counter
    _request_duration_sec: Histogram

    def __init__(self) -> None:
        self._request_count = Counter(
            name="backendai_graphql_request_count",
            documentation="Total number of API requests",
            labelnames=[
                "operation_type",
                "field_name",
                "parent_type",
                "operation_name",
                "domain",
                "operation",
                "error_detail",
                "success",
            ],
        )
        self._request_duration_sec = Histogram(
            name="backendai_graphql_request_duration_sec",
            documentation="Duration of API requests in milliseconds",
            labelnames=[
                "operation_type",
                "field_name",
                "parent_type",
                "operation_name",
                "domain",
                "operation",
                "error_detail",
                "success",
            ],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _inc_request_total(
        self,
        *,
        operation_type: str,
        field_name: str,
        parent_type: str,
        operation_name: str,
        error_code: Optional[ErrorCode],
        success: bool,
    ) -> None:
        self._request_count.labels(
            operation_type=operation_type,
            field_name=field_name,
            parent_type=parent_type,
            operation_name=operation_name,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
            success=success,
        ).inc()

    def _observe_request_duration(
        self,
        *,
        operation_type: str,
        field_name: str,
        parent_type: str,
        operation_name: str,
        error_code: Optional[ErrorCode],
        success: bool,
        duration: float,
    ) -> None:
        self._request_duration_sec.labels(
            operation_type=operation_type,
            field_name=field_name,
            parent_type=parent_type,
            operation_name=operation_name,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
            success=success,
        ).observe(duration)

    def observe_request(
        self,
        *,
        operation_type: str,
        field_name: str,
        parent_type: str,
        operation_name: str,
        error_code: Optional[ErrorCode],
        success: bool,
        duration: float,
    ) -> None:
        self._inc_request_total(
            operation_type=operation_type,
            field_name=field_name,
            parent_type=parent_type,
            operation_name=operation_name,
            error_code=error_code,
            success=success,
        )
        self._observe_request_duration(
            operation_type=operation_type,
            field_name=field_name,
            parent_type=parent_type,
            operation_name=operation_name,
            error_code=error_code,
            success=success,
            duration=duration,
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
            labelnames=["event_type", "exception", "domain", "operation", "error_detail"],
        )
        self._event_processing_time_sec = Histogram(
            name="backendai_event_processing_time_sec",
            documentation="Processing time of events in seconds",
            labelnames=["event_type", "status", "domain", "operation", "error_detail"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_event_success(self, *, event_type: str, duration: float) -> None:
        self._event_count.labels(event_type=event_type).inc()
        self._event_processing_time_sec.labels(
            event_type=event_type,
            status="success",
            domain="",
            operation="",
            error_detail="",
        ).observe(duration)

    def observe_event_failure(
        self,
        *,
        event_type: str,
        duration: float,
        exception: BaseException,
    ) -> None:
        error_code: ErrorCode
        if isinstance(exception, BackendAIError):
            error_code = exception.error_code()
        else:
            error_code = ErrorCode.default()
        exception_name = exception.__class__.__name__
        self._event_failure_count.labels(
            event_type=event_type,
            exception=exception_name,
            domain=error_code.domain,
            operation=error_code.operation,
            error_detail=error_code.error_detail,
        ).inc()
        self._event_count.labels(event_type=event_type).inc()
        self._event_processing_time_sec.labels(
            event_type=event_type,
            status="failure",
            domain=error_code.domain,
            operation=error_code.operation,
            error_detail=error_code.error_detail,
        ).observe(duration)


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
            labelnames=["task_name", "status", "domain", "operation", "error_detail"],
        )
        self._bgtask_processing_time = Histogram(
            name="backendai_bgtask_processing_time_sec",
            documentation="Processing time of background tasks in seconds",
            labelnames=["task_name", "status", "domain", "operation", "error_detail"],
            buckets=[0.1, 1, 10, 30, 60, 300, 600],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_bgtask_started(self, *, task_name: str) -> None:
        self._bgtask_count.labels(task_name=task_name).inc()

    def observe_bgtask_done(
        self, *, task_name: str, status: str, duration: float, error_code: Optional[ErrorCode]
    ) -> None:
        self._bgtask_count.labels(task_name=task_name).dec()
        self._bgtask_processing_time.labels(
            task_name=task_name,
            status=status,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
        ).observe(duration)
        self._bgtask_done_count.labels(
            task_name=task_name,
            status=status,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
        ).inc()


class ActionMetricObserver:
    _instance: Optional[Self] = None

    _action_count: Counter
    _action_duration_sec: Histogram

    def __init__(self) -> None:
        self._action_count = Counter(
            name="backendai_action_count",
            documentation="Total number of actions",
            labelnames=[
                "entity_type",
                "operation_type",
                "status",
                "domain",
                "operation",
                "error_detail",
            ],
        )
        self._action_duration_sec = Histogram(
            name="backendai_action_duration_sec",
            documentation="Duration of actions in seconds",
            labelnames=[
                "entity_type",
                "operation_type",
                "status",
                "domain",
                "operation",
                "error_detail",
            ],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_action(
        self,
        *,
        entity_type: str,
        operation_type: str,
        status: str,
        duration: float,
        error_code: Optional[ErrorCode],
    ) -> None:
        self._action_count.labels(
            entity_type=entity_type,
            operation_type=operation_type,
            status=status,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
        ).inc()
        self._action_duration_sec.labels(
            entity_type=entity_type,
            operation_type=operation_type,
            status=status,
            domain=error_code.domain if error_code else "",
            operation=error_code.operation if error_code else "",
            error_detail=error_code.error_detail if error_code else "",
        ).observe(duration)


class DomainType(enum.StrEnum):
    VALKEY = "valkey"
    REPOSITORY = "repository"
    CLIENT = "client"


class LayerType(enum.StrEnum):
    # Repository layers
    AGENT = "agent"
    AUTH = "auth"
    ARTIFACT = "artifact"
    ARTIFACT_REGISTRY = "artifact_registry"
    CONTAINER_REGISTRY = "container_registry"
    DOMAIN = "domain"
    GROUP = "group"
    IMAGE = "image"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"
    METRIC = "metric"
    MODEL_SERVING = "model_serving"
    PROJECT_RESOURCE_POLICY = "project_resource_policy"
    RESOURCE_PRESET = "resource_preset"
    SCHEDULE = "schedule"
    SESSION = "session"
    USER = "user"
    USER_RESOURCE_POLICY = "user_resource_policy"
    VFOLDER = "vfolder"
    PERMISSION_CONTROL = "permission_control"
    OBJECT_STORAGE = "object_storage"

    # Valkey client layers
    VALKEY_CONTAINER_LOG = "valkey_container_log"
    VALKEY_IMAGE = "valkey_image"
    VALKEY_LIVE = "valkey_live"
    VALKEY_RATE_LIMIT = "valkey_rate_limit"
    VALKEY_SCHEDULE = "valkey_schedule"
    VALKEY_SESSION = "valkey_session"
    VALKEY_STAT = "valkey_stat"
    VALKEY_STREAM = "valkey_stream"
    VALKEY_BGTASK = "valkey_bgtask"

    # Client layers
    AGENT_CLIENT = "agent_client"
    STORAGE_PROXY_CLIENT = "storage_proxy_client"
    WSPROXY_CLIENT = "wsproxy_client"


# Backward compatibility
ClientType = DomainType


class LayerMetricObserver:
    _instance: Optional[Self] = None

    _layer_operation_triggered_count: Gauge
    _layer_operation_count: Counter
    _layer_retry_count: Counter
    _layer_operation_duration_sec: Histogram

    def __init__(self) -> None:
        self._layer_operation_triggered_count = Gauge(
            name="backendai_layer_operation_triggered_count",
            documentation="Number of layer operations triggered",
            labelnames=["domain", "layer", "operation"],
        )
        self._layer_operation_count = Counter(
            name="backendai_layer_operation_count",
            documentation="Total number of layer operations",
            labelnames=["domain", "layer", "operation", "success"],
        )
        self._layer_retry_count = Counter(
            name="backendai_layer_retry_count",
            documentation="Number of retries for layer operations",
            labelnames=["domain", "layer", "operation"],
        )
        self._layer_operation_duration_sec = Histogram(
            name="backendai_layer_operation_duration_sec",
            documentation="Duration of layer operations in seconds",
            labelnames=["domain", "layer", "operation", "success"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_layer_operation_triggered(
        self,
        *,
        domain: DomainType,
        layer: LayerType,
        operation: str,
    ) -> None:
        self._layer_operation_triggered_count.labels(
            domain=domain,
            layer=layer,
            operation=operation,
        ).inc()

    def observe_layer_retry(
        self,
        *,
        domain: DomainType,
        layer: LayerType,
        operation: str,
    ) -> None:
        self._layer_retry_count.labels(
            domain=domain,
            layer=layer,
            operation=operation,
        ).inc()

    def observe_layer_operation(
        self,
        *,
        domain: DomainType,
        layer: LayerType,
        operation: str,
        success: bool,
        duration: float,
    ) -> None:
        self._layer_operation_triggered_count.labels(
            domain=domain,
            layer=layer,
            operation=operation,
        ).dec()  # Decrement the triggered count since the operation is now complete
        self._layer_operation_count.labels(
            domain=domain,
            layer=layer,
            operation=operation,
            success=str(success),
        ).inc()
        self._layer_operation_duration_sec.labels(
            domain=domain,
            layer=layer,
            operation=operation,
            success=str(success),
        ).observe(duration)


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


class SweeperMetricObserver:
    _instance: Optional[Self] = None

    _session_sweep_count: Counter
    _kernel_sweep_count: Counter

    def __init__(self) -> None:
        self._session_sweep_count = Counter(
            name="backendai_sweep_session_count",
            documentation="Total number of session sweeps",
            labelnames=["status", "success"],
        )
        self._kernel_sweep_count = Counter(
            name="backendai_sweep_kernel_count",
            documentation="Total number of kernel sweeps",
            labelnames=["success"],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_session_sweep(self, *, status: str, success: bool) -> None:
        self._session_sweep_count.labels(status=status, success=success).inc()

    def observe_kernel_sweep(self, *, success: bool) -> None:
        self._kernel_sweep_count.labels(success=success).inc()


class EventPropagatorMetricObserver:
    _instance: Optional[Self] = None

    _propagator_count: Gauge
    _propagator_alias_count: Gauge
    _propagator_registration_count: Counter
    _propagator_unregistration_count: Counter

    def __init__(self) -> None:
        self._propagator_count = Gauge(
            name="backendai_event_propagator_count",
            documentation="Current number of active event propagators",
        )
        self._propagator_alias_count = Gauge(
            name="backendai_event_propagator_alias_count",
            documentation="Current number of event propagator aliases",
            labelnames=["domain", "alias_id"],
        )
        self._propagator_registration_count = Counter(
            name="backendai_event_propagator_registration_count",
            documentation="Total number of event propagator registrations",
        )
        self._propagator_unregistration_count = Counter(
            name="backendai_event_propagator_unregistration_count",
            documentation="Total number of event propagator unregistrations",
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_propagator_registered(self, *, aliases: list[tuple[str, str]]) -> None:
        self._propagator_count.inc()
        self._propagator_registration_count.inc()
        for domain, alias_id in aliases:
            self._propagator_alias_count.labels(domain=domain, alias_id=alias_id).inc()

    def observe_propagator_unregistered(self, *, aliases: list[tuple[str, str]]) -> None:
        self._propagator_count.dec()
        self._propagator_unregistration_count.inc()
        for domain, alias_id in aliases:
            self._propagator_alias_count.labels(domain=domain, alias_id=alias_id).dec()


class CommonMetricRegistry:
    _instance: Optional[Self] = None

    api: APIMetricObserver
    gql: GraphQLMetricObserver
    event: EventMetricObserver
    bgtask: BgTaskMetricObserver
    system: SystemMetricObserver
    sweeper: SweeperMetricObserver
    event_propagator_observer: EventPropagatorMetricObserver

    def __init__(self) -> None:
        self.api = APIMetricObserver.instance()
        self.gql = GraphQLMetricObserver.instance()
        self.event = EventMetricObserver.instance()
        self.bgtask = BgTaskMetricObserver.instance()
        self.system = SystemMetricObserver.instance()
        self.sweeper = SweeperMetricObserver.instance()
        self.event_propagator_observer = EventPropagatorMetricObserver.instance()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def to_prometheus(self) -> str:
        self.system.observe()
        return generate_latest().decode("utf-8")


class StageObserver:
    _instance: Optional[Self] = None

    _stage_count: Counter

    def __init__(self) -> None:
        self._stage_count = Counter(
            name="backendai_stage_count",
            documentation="Count stage occurrences",
            labelnames=["stage", "upper_layer"],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_stage(self, *, stage: str, upper_layer: str) -> None:
        self._stage_count.labels(stage=stage, upper_layer=upper_layer).inc()
