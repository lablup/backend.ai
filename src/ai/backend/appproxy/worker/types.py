from __future__ import annotations

import asyncio
import dataclasses
import enum
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Callable,
    Final,
    FrozenSet,
    Generic,
    Mapping,
    Optional,
    Self,
    TypeAlias,
    TypeVar,
    Union,
)
from uuid import UUID

import aiohttp_cors
import attrs
import prometheus_client

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    SerializableCircuit,
)
from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.metrics.metric import (
    APIMetricObserver,
    EventMetricObserver,
    SystemMetricObserver,
)
from ai.backend.common.types import (
    MetricKey,
    MetricValue,
    MovingStatValue,
    RuntimeVariant,
)

if TYPE_CHECKING:
    from .config import ServerConfig
    from .proxy.frontend.base import BaseFrontend


class ProxyMetricObserver:
    _instance: Optional[Self] = None

    _upstream_request_sent_http: prometheus_client.Counter
    _upstream_response_received_http: prometheus_client.Counter
    _requests_received_http: prometheus_client.Counter
    _responses_sent_http: prometheus_client.Counter
    _pending_requests_http: prometheus_client.Gauge
    _proxy_request_iteration_duration_http: prometheus_client.Histogram
    _request_body_size_http: prometheus_client.Histogram
    _response_body_size_http: prometheus_client.Histogram

    _connections_established_ws: prometheus_client.Counter
    _connections_closed_ws: prometheus_client.Counter
    _pending_connections_ws: prometheus_client.Gauge
    _proxy_request_iteration_duration_ws: prometheus_client.Histogram
    _connection_processed_traffics_ws: prometheus_client.Counter
    _connection_total_traffics_ws: prometheus_client.Histogram

    _connections_established_tcp: prometheus_client.Counter
    _connections_closed_tcp: prometheus_client.Counter
    _pending_connections_tcp: prometheus_client.Gauge
    _proxy_request_iteration_duration_tcp: prometheus_client.Histogram
    _connection_processed_traffics_tcp: prometheus_client.Counter
    _connection_total_traffics_tcp: prometheus_client.Histogram

    def __init__(self) -> None:
        self._upstream_request_sent_http = prometheus_client.Counter(
            name="appproxy_upstream_request_sent_http",
            labelnames=["remote"],
            documentation="Total number of HTTP requests sent to upstream",
        )
        self._upstream_request_sent_http.labels(remote="").inc(0)
        self._upstream_response_received_http = prometheus_client.Counter(
            name="appproxy_upstream_response_received_http",
            labelnames=["remote"],
            documentation="Total number of HTTP responses received from upstream",
        )
        self._upstream_response_received_http.labels(remote="").inc(0)
        self._requests_received_http = prometheus_client.Counter(
            name="appproxy_requests_received_http",
            labelnames=["remote"],
            documentation="Total number of HTTP requests received from downstream",
        )
        self._requests_received_http.labels(remote="").inc(0)
        self._responses_sent_http = prometheus_client.Counter(
            name="appproxy_responses_sent_http",
            labelnames=["remote"],
            documentation="Total number of HTTP responses sent to downstream",
        )
        self._responses_sent_http.labels(remote="").inc(0)
        self._pending_requests_http = prometheus_client.Gauge(
            name="appproxy_pending_requests_http",
            labelnames=["remote"],
            documentation="Ongoing HTTP proxy requests initiated by downstream",
        )
        self._pending_requests_http.labels(remote="").set(0)
        self._proxy_request_iteration_duration_http = prometheus_client.Histogram(
            name="appproxy_proxy_request_iteration_duration_http",
            labelnames=["remote"],
            documentation="Total seconds taken to complete each HTTP proxy request",
        )
        self._request_body_size_http = prometheus_client.Histogram(
            name="appproxy_request_body_size_http",
            labelnames=["remote"],
            documentation="Request body size measured for each HTTP proxy request",
        )
        self._response_body_size_http = prometheus_client.Histogram(
            name="appproxy_response_body_size_http",
            labelnames=["remote"],
            documentation="Byte length of the response body generated from upstream HTTP response",
        )
        self._connections_established_ws = prometheus_client.Counter(
            name="appproxy_connections_established_ws",
            documentation="Total number of WebSocket connections established",
        )
        self._connections_established_ws.inc(0)
        self._connections_closed_ws = prometheus_client.Counter(
            name="appproxy_connections_closed_ws",
            documentation="Total number of WebSocket connections closed",
        )
        self._connections_closed_ws.inc(0)
        self._pending_connections_ws = prometheus_client.Gauge(
            name="appproxy_pending_connections_ws",
            documentation="Ongoing WebSocket proxy connections",
        )
        self._pending_connections_ws.set(0)
        self._proxy_request_iteration_duration_ws = prometheus_client.Histogram(
            name="appproxy_proxy_request_iteration_duration_ws",
            documentation="Total seconds taken to complete each WebSocket proxy request",
        )
        self._connection_processed_traffics_ws = prometheus_client.Counter(
            name="appproxy_connection_processed_traffics_ws",
            documentation="Number of bytes transferred from each WebSocket connection bidirectionally, updated on-the-fly",
        )
        self._connection_processed_traffics_ws.inc(0)
        self._connection_total_traffics_ws = prometheus_client.Histogram(
            name="appproxy_connection_total_traffics_ws",
            documentation="Number of bytes transferred from each WebSocket connection bidirectionally, updated after WebSocket connection closes",
        )
        self._connections_established_tcp = prometheus_client.Counter(
            name="appproxy_connections_established_tcp",
            documentation="Total number of TCP connections established",
        )
        self._connections_established_tcp.inc(0)
        self._connections_closed_tcp = prometheus_client.Counter(
            name="appproxy_connections_closed_tcp",
            documentation="Total number of TCP connections closed",
        )
        self._connections_closed_tcp.inc(0)
        self._pending_connections_tcp = prometheus_client.Gauge(
            name="appproxy_pending_connections_tcp",
            documentation="Ongoing TCP proxy connections",
        )
        self._pending_connections_tcp.set(0)
        self._proxy_request_iteration_duration_tcp = prometheus_client.Histogram(
            name="appproxy_proxy_request_iteration_duration_tcp",
            documentation="Total seconds taken to complete each TCP proxy request",
        )
        self._connection_processed_traffics_tcp = prometheus_client.Counter(
            name="appproxy_connection_processed_traffics_tcp",
            documentation="Number of bytes transferred from each TCP connection bidirectionally, updated on-the-fly",
        )
        self._connection_processed_traffics_tcp.inc(0)
        self._connection_total_traffics_tcp = prometheus_client.Histogram(
            name="appproxy_connection_total_traffics_tcp",
            documentation="Number of bytes transferred from each TCP connection bidirectionally, updated on-the-fly",
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_upstream_http_request(self, *, remote: str, total_bytes_size: int) -> None:
        self._upstream_request_sent_http.labels(remote=remote).inc()
        self._request_body_size_http.labels(remote=remote).observe(total_bytes_size)

    def observe_upstream_http_response(self, *, remote: str, total_bytes_size: int) -> None:
        self._upstream_response_received_http.labels(remote=remote).inc()
        self._response_body_size_http.labels(remote=remote).observe(total_bytes_size)

    def observe_downstream_http_request(self, *, remote: str) -> None:
        self._requests_received_http.labels(remote=remote).inc()
        self._pending_requests_http.labels(remote=remote).inc()

    def observe_downstream_http_response(self, *, remote: str, duration: int) -> None:
        self._pending_requests_http.labels(remote=remote).dec()
        self._proxy_request_iteration_duration_http.labels(remote=remote).observe(duration)
        self._responses_sent_http.labels(remote=remote).inc()

    def observe_upstream_ws_traffic_chunk(self, *, total_bytes_size: int) -> None:
        self._connection_processed_traffics_ws.inc(total_bytes_size)

    def observe_upstream_ws_connection_start(self) -> None:
        self._connections_established_ws.inc()
        self._pending_connections_ws.inc()

    def observe_upstream_ws_connection_end(self, *, duration: int, total_bytes_size: int) -> None:
        self._connections_closed_ws.inc()
        self._pending_connections_ws.dec()
        self._proxy_request_iteration_duration_ws.observe(duration)
        self._connection_total_traffics_ws.observe(total_bytes_size)

    def observe_upstream_tcp_traffic_chunk(self, total_bytes_size: int) -> None:
        self._connection_processed_traffics_tcp.inc(total_bytes_size)

    def observe_downstream_tcp_start(self) -> None:
        self._connections_established_tcp.inc()
        self._pending_connections_tcp.inc()

    def observe_downstream_tcp_end(self, *, duration: int) -> None:
        self._connections_closed_tcp.inc()
        self._pending_connections_tcp.dec()
        self._proxy_request_iteration_duration_tcp.observe(duration)


class CircuitMetricObserver:
    _instance: Optional[Self] = None

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    _circuits_created: prometheus_client.Counter
    _alive_circuits: prometheus_client.Gauge

    def __init__(self) -> None:
        self._circuits_created = prometheus_client.Counter(
            name="appproxy_circuits_created",
            labelnames=["protocol"],
            documentation="Total number of AppProxy circuits created on this Worker. `endpoint_id` is provided only when circuit is INFERENCE type. `user_id` is provided only when circuit is INTERACTIVE type.",
        )
        self._circuits_created.labels(protocol="").inc(0)
        self._alive_circuits = prometheus_client.Gauge(
            name="appproxy_alive_circuits",
            labelnames=["protocol"],
            documentation="Total number of AppProxy circuits created on this Worker. `endpoint_id` is provided only when circuit is INFERENCE type. `user_id` is provided only when circuit is INTERACTIVE type.",
        )
        self._alive_circuits.labels(protocol="").set(0)

    def observe_circuit_creation(self, *, protocol: str) -> None:
        self._circuits_created.labels(protocol=protocol).inc()
        self._alive_circuits.labels(protocol=protocol).inc()

    def observe_circuit_removal(self, *, protocol: str) -> None:
        self._alive_circuits.labels(protocol=protocol).dec()


class WorkerMetricRegistry:
    _instance: Optional[Self] = None

    api: APIMetricObserver
    proxy: ProxyMetricObserver
    circuit: CircuitMetricObserver
    event: EventMetricObserver
    system: SystemMetricObserver

    def __init__(self) -> None:
        self.api = APIMetricObserver.instance()
        self.proxy = ProxyMetricObserver.instance()
        self.circuit = CircuitMetricObserver.instance()
        self.event = EventMetricObserver.instance()
        self.system = SystemMetricObserver.instance()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def to_prometheus(self) -> str:
        self.system.observe()
        return prometheus_client.generate_latest().decode("utf-8")


@dataclass
class PrometheusMetrics:
    registry: prometheus_client.CollectorRegistry

    redis_events_received: prometheus_client.Counter
    alive_asyncio_tasks: prometheus_client.Gauge
    memory_used_rss: prometheus_client.Gauge
    memory_used_vms: prometheus_client.Gauge


@attrs.define(slots=True, auto_attribs=True, init=False)
class RootContext:
    pidx: int
    proxy_frontend: BaseFrontend
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    valkey_live: ValkeyLiveClient
    valkey_stat: ValkeyStatClient
    http_client_pool: ClientPool
    worker_id: UUID
    local_config: ServerConfig
    last_used_time_marker_redis_queue: asyncio.Queue[tuple[list[str], float]]
    request_counter_redis_queue: asyncio.Queue[str]
    cors_options: dict[str, aiohttp_cors.ResourceOptions]
    metrics: WorkerMetricRegistry


CleanupContext: TypeAlias = Callable[["RootContext"], AsyncContextManager[None]]
TCircuitKey = TypeVar("TCircuitKey", int, str)


@dataclass
class PortFrontendInfo:
    port: int


@dataclass
class SubdomainFrontendInfo:
    subdomain: str


@dataclass
class InteractiveAppInfo:
    user_id: UUID


@dataclass
class InferenceAppInfo:
    endpoint_id: UUID
    runtime_variant: RuntimeVariant | None


class Circuit(SerializableCircuit):
    frontend: PortFrontendInfo | SubdomainFrontendInfo

    port: int | None
    "for initialization usage only; use `frontend` variable"
    subdomain: str | None
    "for initialization usage only; use `frontend` variable"

    app_info: InteractiveAppInfo | InferenceAppInfo

    user_id: UUID | None
    "for initialization usage only; use `app_info` variable"
    endpoint_id: UUID | None
    "for initialization usage only; use `app_info` variable"
    runtime_variant: str | None
    "for initialization usage only; use `app_info` variable"

    _app_inference_metrics: dict[MetricKey, "Metric | HistogramMetric"]
    _replica_inference_metrics: dict[
        MetricKey, dict[UUID, "Metric | HistogramMetric"]
    ]  # [Metric Key:[Route id: Metric]] pair

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._app_inference_metrics = {}
        self._replica_inference_metrics = {}

    @classmethod
    def from_serialized_circuit(cls, circuit: SerializableCircuit) -> "Circuit":
        frontend: PortFrontendInfo | SubdomainFrontendInfo
        app_info: InteractiveAppInfo | InferenceAppInfo

        match circuit.app_mode:
            case AppMode.INTERACTIVE:
                assert circuit.user_id
                app_info = InteractiveAppInfo(circuit.user_id)
            case AppMode.INFERENCE:
                assert circuit.endpoint_id
                app_info = InferenceAppInfo(
                    circuit.endpoint_id,
                    RuntimeVariant(circuit.runtime_variant)
                    if circuit.runtime_variant is not None
                    else None,
                )

        match circuit.frontend_mode:
            case FrontendMode.PORT:
                assert circuit.port is not None
                frontend = PortFrontendInfo(circuit.port)
            case FrontendMode.WILDCARD_DOMAIN:
                assert circuit.subdomain is not None
                frontend = SubdomainFrontendInfo(circuit.subdomain)

        return cls(frontend=frontend, app_info=app_info, **circuit.model_dump())

    @property
    def prometheus_metric_label(self) -> dict[str, str]:
        metric_labels = {"protocol": self.protocol.name}

        return metric_labels


class MetricTypes(enum.Enum):
    """
    Specifies the type of a metric value.

    Currently this DOES NOT affect calculation and processing of the metric,
    but serves as a metadata for code readers.
    The actual calculation and formatting is controlled by :meth:`Metric.current_hook()`,
    :attr:`Metric.unit_hint` and :attr:`Metric.stats_filter`.
    """

    GAUGE = 0
    """
    Represents an instantly measured occupancy value.
    (e.g., used space as bytes, occupied amount as the number of items or a bandwidth)
    """

    # Enum value 1 and 2 intentionally left unused to match consistency with agent statistics

    ACCUMULATION = 3
    """
    Represents an accumulated value
    (e.g., total number of events, total period of occupation)
    """
    HISTOGRAM = 4
    """
    Represents a histogram of values
    (e.g., latency distribution)
    """


@dataclass
class Measurement:
    value: Decimal
    capacity: Optional[Decimal] = dataclasses.field(default=None)


@dataclass
class HistogramMeasurement:
    buckets: Mapping[str, Decimal]
    count: Optional[int] = dataclasses.field(default=None)
    sum: Optional[Decimal] = dataclasses.field(default=None)


TMeasurement = TypeVar("TMeasurement", bound=Union[Measurement, HistogramMeasurement])


@dataclass
class InferenceMeasurement(Generic[TMeasurement]):
    """
    Collection of per-inference framework statistics for a specific metric.
    """

    key: MetricKey
    type: MetricTypes
    per_app: TMeasurement
    per_replica: Mapping[UUID, TMeasurement]  # [Route Id: Measurement] pair
    stats_filter: FrozenSet[str] = dataclasses.field(default_factory=frozenset)
    unit_hint: str = dataclasses.field(default="count")


def remove_exponent(num: Decimal) -> Decimal:
    return num.quantize(Decimal(1)) if num == num.to_integral() else num.normalize()


class MovingStatistics:
    __slots__ = (
        "_sum",
        "_count",
        "_min",
        "_max",
        "_last",
    )
    _sum: Decimal
    _count: int
    _min: Decimal
    _max: Decimal
    _last: list[tuple[Decimal, float]]

    def __init__(self, initial_value: Optional[Decimal] = None):
        self._last = []
        if initial_value is None:
            self._sum = Decimal(0)
            self._min = Decimal("inf")
            self._max = Decimal("-inf")
            self._count = 0
        else:
            self._sum = initial_value
            self._min = initial_value
            self._max = initial_value
            self._count = 1
            point = (initial_value, time.perf_counter())
            self._last.append(point)

    def update(self, value: Decimal):
        self._sum += value
        self._min = min(self._min, value)
        self._max = max(self._max, value)
        self._count += 1
        point = (value, time.perf_counter())
        self._last.append(point)
        # keep only the latest two data points
        if len(self._last) > 2:
            self._last.pop(0)

    @property
    def min(self) -> Decimal:
        return self._min

    @property
    def max(self) -> Decimal:
        return self._max

    @property
    def sum(self) -> Decimal:
        return self._sum

    @property
    def avg(self) -> Decimal:
        return self._sum / self._count

    @property
    def diff(self) -> Decimal:
        if len(self._last) == 2:
            return self._last[-1][0] - self._last[-2][0]
        return Decimal(0)

    @property
    def rate(self) -> Decimal:
        if len(self._last) == 2:
            return (self._last[-1][0] - self._last[-2][0]) / Decimal(
                self._last[-1][1] - self._last[-2][1]
            )
        return Decimal(0)

    def to_serializable_dict(self) -> MovingStatValue:
        q = Decimal("0.000")
        return {
            "min": str(remove_exponent(self.min.quantize(q))),
            "max": str(remove_exponent(self.max.quantize(q))),
            "sum": str(remove_exponent(self.sum.quantize(q))),
            "avg": str(remove_exponent(self.avg.quantize(q))),
            "diff": str(remove_exponent(self.diff.quantize(q))),
            "rate": str(remove_exponent(self.rate.quantize(q))),
            "version": 2,
        }


@attrs.define(auto_attribs=True, slots=True)
class Metric:
    key: str
    type: MetricTypes
    unit_hint: str
    stats: MovingStatistics
    stats_filter: FrozenSet[str]
    current: Decimal
    capacity: Optional[Decimal] = None
    current_hook: Optional[Callable[["Metric"], Decimal]] = None

    def update(self, value: Measurement):
        if value.capacity is not None:
            self.capacity = value.capacity
        self.stats.update(value.value)
        self.current = value.value
        if self.current_hook is not None:
            self.current = self.current_hook(self)

    def to_serializable_dict(self) -> MetricValue:
        q = Decimal("0.000")
        q_pct = Decimal("0.00")
        return {
            "__type": self.type.name,  # type: ignore
            "current": str(remove_exponent(self.current.quantize(q))),
            "capacity": (
                str(remove_exponent(self.capacity.quantize(q)))
                if self.capacity is not None
                else None
            ),
            "pct": (
                str(
                    remove_exponent(
                        (Decimal(self.current) / Decimal(self.capacity) * 100).quantize(q_pct)
                    )
                )
                if (self.capacity is not None and self.capacity.is_normal() and self.capacity > 0)
                else "0.00"
            ),
            "unit_hint": self.unit_hint,
            **{
                f"stats.{k}": v  # type: ignore
                for k, v in self.stats.to_serializable_dict().items()
                if k in self.stats_filter
            },
        }


@attrs.define(auto_attribs=True, slots=True)
class HistogramMetric:
    key: str
    threshold_unit: str
    buckets: Mapping[str, Decimal]
    count: Optional[int]
    sum: Optional[Decimal]

    type = MetricTypes.HISTOGRAM

    def update(
        self,
        buckets: Mapping[str, Decimal],
        count: Optional[int] = None,
        sum: Optional[Decimal] = None,
    ):
        self.buckets = buckets
        self.count = count
        self.sum = sum

    def to_serializable_dict(self) -> Mapping[str, Any]:
        return {
            "__type": self.type.name,
            "current": {k: str(v) for k, v in self.buckets.items()},
            "threshold_unit": self.threshold_unit,
            "count": self.count,
            "sum": str(self.sum) if self.sum is not None else None,
        }


class FrontendServerMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"
    TRAEFIK = "traefik"


LAST_USED_MARKER_SOCKET_NAME: Final[str] = "last-used-time-marker.socket"
