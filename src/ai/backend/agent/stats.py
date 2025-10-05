"""
A module to collect various performance metrics of Docker containers.

Reference: https://www.datadoghq.com/blog/how-to-collect-docker-metrics/
"""

import asyncio
import enum
import logging
import sys
import time
import uuid
from decimal import Decimal, DecimalException
from typing import (
    TYPE_CHECKING,
    Callable,
    FrozenSet,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import aiodocker
import attrs

from ai.backend.common import msgpack
from ai.backend.common.identity import is_containerized
from ai.backend.common.metrics.metric import StageObserver
from ai.backend.common.types import (
    PID,
    ContainerId,
    DeviceId,
    KernelId,
    MetricKey,
    MetricValue,
    MovingStatValue,
    SessionId,
)
from ai.backend.logging import BraceStyleAdapter

from .metrics.metric import UtilizationMetricObserver
from .metrics.types import (
    CAPACITY_METRIC_KEY,
    CURRENT_METRIC_KEY,
    PCT_METRIC_KEY,
    FlattenedDeviceMetric,
    FlattenedKernelMetric,
)
from .utils import remove_exponent

if TYPE_CHECKING:
    from .agent import AbstractAgent
    from .kernel import AbstractKernel

__all__ = (
    "StatContext",
    "StatModes",
    "MetricTypes",
    "NodeMeasurement",
    "ContainerMeasurement",
    "Measurement",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def check_cgroup_available():
    """
    Check if the host OS provides cgroups.
    """
    return not is_containerized() and sys.platform.startswith("linux")


class StatModes(enum.StrEnum):
    CGROUP = "cgroup"
    DOCKER = "docker"

    @staticmethod
    def get_preferred_mode():
        """
        Returns the most preferred statistics collector type for the host OS.
        """
        if check_cgroup_available():
            return StatModes.CGROUP
        return StatModes.DOCKER


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
    USAGE = 0
    """
    This is same to GAUGE, but just kept for backward compatibility of compute plugins.
    """
    RATE = 1
    """
    Represents a rate of changes calculated from underlying gauge/accumulation values
    (e.g., I/O bps calculated from RX/TX accum.bytes)
    """
    UTILIZATION = 2
    """
    Represents a ratio of resource occupation time per each measurement interval
    (e.g., CPU utilization)
    """
    ACCUMULATION = 3
    """
    Represents an accumulated value
    (e.g., total number of events, total period of occupation)
    """


@attrs.define(auto_attribs=True, slots=True)
class Measurement:
    value: Decimal
    capacity: Optional[Decimal] = None


@attrs.define(auto_attribs=True, slots=True)
class NodeMeasurement:
    """
    Collection of per-node and per-agent statistics for a specific metric.
    """

    # 2-tuple of Decimals mean raw values for (usage, available)
    # Percent values are calculated from them.
    key: MetricKey
    type: MetricTypes
    per_node: Measurement
    per_device: Mapping[DeviceId, Measurement] = attrs.Factory(dict)
    stats_filter: FrozenSet[str] = attrs.Factory(frozenset)
    current_hook: Optional[Callable[["Metric"], Decimal]] = None
    unit_hint: str = "count"


@attrs.define(auto_attribs=True, slots=True)
class ContainerMeasurement:
    """
    Collection of per-container statistics for a specific metric.
    """

    key: MetricKey
    type: MetricTypes
    per_container: Mapping[str, Measurement] = attrs.Factory(dict)
    stats_filter: FrozenSet[str] = attrs.Factory(frozenset)
    current_hook: Optional[Callable[["Metric"], Decimal]] = None
    unit_hint: str = "count"


@attrs.define(auto_attribs=True, slots=True)
class ProcessMeasurement:
    """
    Collection of per-process statistics for a specific metric.
    """

    key: MetricKey
    type: MetricTypes
    per_process: Mapping[int, Measurement] = attrs.Factory(dict)
    stats_filter: FrozenSet[str] = attrs.Factory(frozenset)
    current_hook: Optional[Callable[["Metric"], Decimal]] = None
    unit_hint: str = "count"


def _to_serializable_value(value: Decimal, *, exponent: Decimal = Decimal("0.000")) -> str:
    """
    Convert a Decimal value to a string without scientific notation.
    """
    try:
        quantized = value.quantize(exponent)
    except DecimalException:
        return str(value)
    try:
        return str(remove_exponent(quantized))
    except DecimalException:
        return str(quantized)


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
    _last: List[Tuple[Decimal, float]]

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
        return {
            "min": _to_serializable_value(self.min),
            "max": _to_serializable_value(self.max),
            "sum": _to_serializable_value(self.sum),
            "avg": _to_serializable_value(self.avg),
            "diff": _to_serializable_value(self.diff),
            "rate": _to_serializable_value(self.rate),
            "version": 2,
        }

    def __str__(self) -> str:
        return str({
            "min": self.min,
            "max": self.max,
            "sum": self.sum,
            "avg": self.avg,
            "diff": self.diff,
            "rate": self.rate,
        })


@attrs.define(auto_attribs=True, slots=True)
class Metric:
    key: str  # MetricKey
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
        q_pct = Decimal("0.00")
        return {
            "current": _to_serializable_value(self.current),
            "capacity": (
                _to_serializable_value(self.capacity) if self.capacity is not None else None
            ),
            "pct": (
                _to_serializable_value(
                    (Decimal(self.current) / Decimal(self.capacity) * 100), exponent=q_pct
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


class StatContext:
    agent: "AbstractAgent"
    mode: StatModes
    node_metrics: dict[MetricKey, Metric]
    device_metrics: dict[MetricKey, dict[DeviceId, Metric]]
    kernel_metrics: dict[KernelId, dict[MetricKey, Metric]]
    process_metrics: dict[ContainerId, dict[PID, dict[MetricKey, Metric]]]
    _utilization_metric_observer: UtilizationMetricObserver
    _stage_observer: StageObserver

    def __init__(
        self, agent: "AbstractAgent", mode: Optional[StatModes] = None, *, cache_lifespan: int = 120
    ) -> None:
        self.agent = agent
        self.mode = mode if mode is not None else StatModes.get_preferred_mode()
        self.cache_lifespan = cache_lifespan

        self.node_metrics = {}
        self.device_metrics = {}
        self.kernel_metrics = {}
        self.process_metrics = {}

        self._lock = asyncio.Lock()
        self._timestamps: MutableMapping[str, float] = {}
        self._utilization_metric_observer = UtilizationMetricObserver.instance()
        self._stage_observer = StageObserver.instance()

    def update_timestamp(self, timestamp_key: str) -> Tuple[float, float]:
        """
        Update the timestamp for the given key and return a pair of the current timestamp and
        the interval from the last update of the same key.

        If the last timestamp for the given key does not exist, the interval becomes "NaN".

        Intended to be used by compute plugins.
        """
        now = time.perf_counter()
        last = self._timestamps.get(timestamp_key, None)
        self._timestamps[timestamp_key] = now
        if last is None:
            return now, 0.0
        return now, now - last

    def _get_ownership_info_from_kernel(
        self,
        kernel_id: KernelId,
    ) -> tuple[Optional[SessionId], Optional[uuid.UUID], Optional[uuid.UUID]]:
        kernel_obj = self.agent.kernel_registry.get(kernel_id)
        if kernel_obj is not None:
            ownership_data = kernel_obj.ownership_data
            session_id = ownership_data.session_id
            owner_user_id = ownership_data.owner_user_id
            owner_project_id = ownership_data.owner_project_id
        else:
            session_id = None
            owner_user_id = None
            owner_project_id = None
        return session_id, owner_user_id, owner_project_id

    def observe_node_metric(
        self,
        device_id: DeviceId,
        metric_key: MetricKey,
        measure: Measurement,
    ) -> None:
        agent_id = self.agent.id
        value_pairs = [
            (CURRENT_METRIC_KEY, str(measure.value)),
        ]
        if measure.capacity is not None:
            value_pairs.append((CAPACITY_METRIC_KEY, str(measure.capacity)))
        self._utilization_metric_observer.observe_device_metric(
            metric=FlattenedDeviceMetric(
                agent_id=agent_id,
                device_id=device_id,
                key=metric_key,
                value_pairs=value_pairs,
            )
        )

    async def remove_kernel_metric(self, kernel_id: KernelId) -> None:
        log.info("Removing metrics for kernel {}", kernel_id)
        known_metrics = self.kernel_metrics.get(kernel_id)
        log.debug("Known metrics for kernel {}: {}", kernel_id, known_metrics)
        if known_metrics is None:
            return
        metric_keys = list(known_metrics.keys())
        agent_id = self.agent.id
        session_id, owner_user_id, project_id = self._get_ownership_info_from_kernel(kernel_id)
        await self._utilization_metric_observer.lazy_remove_container_metric(
            agent_id=agent_id,
            kernel_id=kernel_id,
            session_id=session_id,
            owner_user_id=owner_user_id,
            project_id=project_id,
            keys=metric_keys,
        )

    async def collect_node_stat(self) -> None:
        """
        Collect the per-node, per-device, and per-container statistics.

        Intended to be used by the agent.
        """
        self._stage_observer.observe_stage(
            stage="before_lock",
            upper_layer="collect_node_stat",
        )
        async with self._lock:
            # Here we use asyncio.gather() instead of aiotools.TaskGroup
            # to keep methods of other plugins running when a plugin raises an error
            # instead of cancelling them.
            _tasks: list[asyncio.Task[Sequence[NodeMeasurement]]] = []
            for computer in self.agent.computers.values():
                _tasks.append(asyncio.create_task(computer.instance.gather_node_measures(self)))
            self._stage_observer.observe_stage(
                stage="before_gather_measures",
                upper_layer="collect_node_stat",
            )
            results = await asyncio.gather(*_tasks, return_exceptions=True)
            self._stage_observer.observe_stage(
                stage="before_observe",
                upper_layer="collect_node_stat",
            )
            for result in results:
                if isinstance(result, BaseException):
                    log.error("collect_node_stat(): gather_node_measures() error", exc_info=result)
                    continue
                for node_measure in result:
                    metric_key = node_measure.key
                    # update node metric
                    if metric_key not in self.node_metrics:
                        self.node_metrics[metric_key] = Metric(
                            metric_key,
                            node_measure.type,
                            current=node_measure.per_node.value,
                            capacity=node_measure.per_node.capacity,
                            unit_hint=node_measure.unit_hint,
                            stats=MovingStatistics(node_measure.per_node.value),
                            stats_filter=frozenset(node_measure.stats_filter),
                            current_hook=node_measure.current_hook,
                        )
                    else:
                        self.node_metrics[metric_key].update(node_measure.per_node)
                    # update per-device metric
                    for dev_id, measure in node_measure.per_device.items():
                        self.observe_node_metric(
                            device_id=dev_id,
                            metric_key=metric_key,
                            measure=measure,
                        )
                        if metric_key not in self.device_metrics:
                            self.device_metrics[metric_key] = {}
                        if dev_id not in self.device_metrics[metric_key]:
                            self.device_metrics[metric_key][dev_id] = Metric(
                                metric_key,
                                node_measure.type,
                                current=measure.value,
                                capacity=measure.capacity,
                                unit_hint=node_measure.unit_hint,
                                stats=MovingStatistics(measure.value),
                                stats_filter=frozenset(node_measure.stats_filter),
                                current_hook=node_measure.current_hook,
                            )
                        else:
                            self.device_metrics[metric_key][dev_id].update(measure)
        agent_id = self.agent.id
        device_metrics: dict[MetricKey, dict[DeviceId, MetricValue]] = {}
        flattened_metrics: list[FlattenedDeviceMetric] = []
        for metric_key, per_device in self.device_metrics.items():
            if metric_key not in device_metrics:
                device_metrics[metric_key] = {}
            for device_id, obj in per_device.items():
                try:
                    metric_value = obj.to_serializable_dict()
                except ValueError:
                    log.warning(
                        "Failed to serialize metric (Device Id: {}, {})", device_id, str(obj.stats)
                    )
                    continue
                device_metrics[metric_key][device_id] = metric_value
                value_pairs = [
                    (CURRENT_METRIC_KEY, metric_value["current"]),
                    (PCT_METRIC_KEY, metric_value["pct"]),
                ]
                if (capacity := metric_value["capacity"]) is not None:
                    value_pairs.append((CAPACITY_METRIC_KEY, capacity))
                flattened_metrics.append(
                    FlattenedDeviceMetric(
                        agent_id,
                        device_id,
                        metric_key,
                        value_pairs,
                    )
                )

        # push to the Redis server
        node_metrics: dict[MetricKey, MetricValue] = {}
        for key, obj in self.node_metrics.items():
            try:
                node_metrics[key] = obj.to_serializable_dict()
            except ValueError:
                log.warning(
                    "Failed to serialize node metric (Metric key: {}, {})", key, str(obj.stats)
                )
                continue

        redis_agent_updates = {
            "node": node_metrics,
            "devices": device_metrics,
        }
        if self.agent.local_config.debug.log_stats:
            log.debug(
                "stats: node_updates: {0}: {1}",
                self.agent.id,
                redis_agent_updates["node"],
            )
        serialized_agent_updates = msgpack.packb(redis_agent_updates)

        self._stage_observer.observe_stage(
            stage="before_report_to_redis",
            upper_layer="collect_node_stat",
        )

        # Use ValkeyStatClient set method with expiration
        agent_id = self.agent.id
        await self.agent.valkey_stat_client.set(
            agent_id, serialized_agent_updates, expire_sec=self.cache_lifespan
        )

    def observe_container_metric(
        self,
        kernel_id: KernelId,
        metric_key: MetricKey,
        measure: Measurement,
    ) -> None:
        agent_id = self.agent.id
        session_id, owner_user_id, project_id = self._get_ownership_info_from_kernel(kernel_id)
        value_pairs = [
            (CURRENT_METRIC_KEY, str(measure.value)),
        ]
        if measure.capacity is not None:
            value_pairs.append((CAPACITY_METRIC_KEY, str(measure.capacity)))
        self._utilization_metric_observer.observe_container_metric(
            metric=FlattenedKernelMetric(
                agent_id=agent_id,
                kernel_id=kernel_id,
                session_id=session_id,
                owner_user_id=owner_user_id,
                project_id=project_id,
                key=metric_key,
                value_pairs=value_pairs,
            )
        )

    async def collect_container_stat(
        self,
        container_ids: Sequence[ContainerId],
    ) -> None:
        """
        Collect the per-container statistics only,

        Intended to be used by the agent and triggered by container cgroup synchronization processes.
        """
        self._stage_observer.observe_stage(
            stage="before_lock",
            upper_layer="collect_container_stat",
        )
        async with self._lock:
            kernel_id_map: dict[ContainerId, KernelId] = {}
            kernel_obj_map: dict[KernelId, AbstractKernel] = {}
            for kid, info in self.agent.kernel_registry.items():
                try:
                    cid = info["container_id"]
                except KeyError:
                    log.warning("collect_container_stat(): no container for kernel {}", kid)
                else:
                    kernel_id_map[ContainerId(cid)] = kid
                    kernel_obj_map[kid] = info
            unused_kernel_ids = set(self.kernel_metrics.keys()) - set(kernel_id_map.values())
            for unused_kernel_id in unused_kernel_ids:
                log.debug("removing kernel_metric for {}", unused_kernel_id)
                self.kernel_metrics.pop(unused_kernel_id, None)

            # Here we use asyncio.gather() instead of aiotools.TaskGroup
            # to keep methods of other plugins running when a plugin raises an error
            # instead of cancelling them.
            _tasks: list[asyncio.Task[Sequence[ContainerMeasurement]]] = []
            kernel_id = None
            for computer in self.agent.computers.values():
                _tasks.append(
                    asyncio.create_task(
                        computer.instance.gather_container_measures(self, container_ids),
                    )
                )
            self._stage_observer.observe_stage(
                stage="before_gather_measures",
                upper_layer="collect_container_stat",
            )
            results = await asyncio.gather(*_tasks, return_exceptions=True)
            updated_kernel_ids: Set[KernelId] = set()
            self._stage_observer.observe_stage(
                stage="before_observe",
                upper_layer="collect_container_stat",
            )
            for result in results:
                if isinstance(result, BaseException):
                    log.error(
                        "collect_container_stat(): gather_container_measures() error",
                        exc_info=result,
                    )
                    continue
                for ctnr_measure in result:
                    assert isinstance(ctnr_measure, ContainerMeasurement)
                    metric_key = ctnr_measure.key
                    # update per-container metric
                    for cid, measure in ctnr_measure.per_container.items():
                        try:
                            kernel_id = kernel_id_map[ContainerId(cid)]
                        except KeyError:
                            continue
                        self.observe_container_metric(
                            kernel_id,
                            metric_key,
                            measure,
                        )
                        updated_kernel_ids.add(kernel_id)
                        if kernel_id not in self.kernel_metrics:
                            self.kernel_metrics[kernel_id] = {}
                        if metric_key not in self.kernel_metrics[kernel_id]:
                            self.kernel_metrics[kernel_id][metric_key] = Metric(
                                metric_key,
                                ctnr_measure.type,
                                current=measure.value,
                                capacity=measure.capacity or measure.value,
                                unit_hint=ctnr_measure.unit_hint,
                                stats=MovingStatistics(measure.value),
                                stats_filter=frozenset(ctnr_measure.stats_filter),
                                current_hook=ctnr_measure.current_hook,
                            )
                        else:
                            self.kernel_metrics[kernel_id][metric_key].update(measure)

        kernel_updates: list[FlattenedKernelMetric] = []
        kernel_serialized_updates: list[tuple[KernelId, bytes]] = []
        agent_id = self.agent.id
        for kernel_id in updated_kernel_ids:
            session_id, owner_user_id, project_id = self._get_ownership_info_from_kernel(kernel_id)
            metrics = self.kernel_metrics[kernel_id]
            serializable_metrics: dict[MetricKey, MetricValue] = {}
            for key, obj in metrics.items():
                try:
                    metric_value = obj.to_serializable_dict()
                except ValueError:
                    log.warning(
                        "Failed to serialize metric (Metric key: {}, {})", key, str(obj.stats)
                    )
                    continue
                serializable_metrics[key] = metric_value
                value_pairs = [
                    (CURRENT_METRIC_KEY, metric_value["current"]),
                    (PCT_METRIC_KEY, metric_value["pct"]),
                ]
                if (capacity := metric_value["capacity"]) is not None:
                    value_pairs.append((CAPACITY_METRIC_KEY, capacity))
                kernel_updates.append(
                    FlattenedKernelMetric(
                        agent_id,
                        kernel_id,
                        session_id,
                        owner_user_id,
                        project_id,
                        key,
                        value_pairs,
                    )
                )
            if self.agent.local_config.debug.log_stats:
                log.debug("kernel_updates: {0}: {1}", kernel_id, serializable_metrics)

            kernel_serialized_updates.append((kernel_id, msgpack.packb(serializable_metrics)))

        self._stage_observer.observe_stage(
            stage="before_report_to_redis",
            upper_layer="collect_container_stat",
        )

        # Use ValkeyStatClient set_multiple_keys for batch operations
        key_value_map = {str(kernel_id): update for kernel_id, update in kernel_serialized_updates}
        if key_value_map:
            await self.agent.valkey_stat_client.set_multiple_keys(key_value_map)

    async def _get_processes(
        self, container_id: ContainerId, docker: aiodocker.Docker
    ) -> list[PID]:
        """
        Get the list of PIDs for the given container ID.
        """
        return_val: list[PID] = []
        try:
            result = await docker._query_json(f"containers/{container_id}/top", method="GET")
            procs = result["Processes"]
        except (KeyError, aiodocker.exceptions.DockerError):
            log.debug(
                "collect_per_container_process_stat(): cannot find container {}", container_id
            )
            return return_val

        for proc in procs:
            try:
                return_val.append(PID(int(proc[1])))
            except (ValueError, KeyError):
                log.debug(
                    "collect_per_container_process_stat(): cannot parse PID from {}",
                    proc,
                )
                continue
        return return_val

    async def collect_per_container_process_stat(
        self,
        container_ids: Sequence[ContainerId],
    ) -> None:
        """
        Collect the per-container process statistics only,

        Intended to be used by the agent.
        """
        # FIXME: support Docker Desktop backend (#1230)
        if sys.platform == "darwin":
            return

        self._stage_observer.observe_stage(
            stage="before_lock",
            upper_layer="collect_per_container_process_stat",
        )
        async with self._lock:
            pid_map: dict[PID, ContainerId] = {}
            async with aiodocker.Docker() as docker:
                for cid in container_ids:
                    active_pids = await self._get_processes(cid, docker)
                    if cid in self.process_metrics:
                        unused_pids = set(self.process_metrics[cid].keys()) - set(active_pids)
                        if unused_pids:
                            log.debug(
                                "removing pid_metric for {}: {}",
                                cid,
                                ", ".join([str(p) for p in unused_pids]),
                            )
                            self.process_metrics[cid] = {
                                pid_: metric
                                for pid_, metric in self.process_metrics[cid].items()
                                if pid_ in active_pids
                            }
                    for pid_ in active_pids:
                        pid_map[pid_] = cid
            # Here we use asyncio.gather() instead of aiotools.TaskGroup
            # to keep methods of other plugins running when a plugin raises an error
            # instead of cancelling them.
            _tasks: list[asyncio.Task[Sequence[ProcessMeasurement]]] = []
            for computer in self.agent.computers.values():
                _tasks.append(
                    asyncio.create_task(
                        computer.instance.gather_process_measures(
                            self, cast(Mapping[int, str], pid_map)
                        ),
                    )
                )
            self._stage_observer.observe_stage(
                stage="before_gather_measures",
                upper_layer="collect_per_container_process_stat",
            )
            results = await asyncio.gather(*_tasks, return_exceptions=True)
            self._stage_observer.observe_stage(
                stage="before_observe",
                upper_layer="collect_per_container_process_stat",
            )
            updated_cids: Set[ContainerId] = set()
            for result in results:
                if isinstance(result, BaseException):
                    log.error(
                        "collect_per_container_process_stat(): gather_process_measures() error",
                        exc_info=result,
                    )
                    continue
                for proc_measure in result:
                    metric_key = proc_measure.key
                    # update per-process metric
                    for pid, measure in proc_measure.per_process.items():
                        pid = PID(pid)
                        cid = pid_map[pid]
                        updated_cids.add(cid)
                        if cid not in self.process_metrics:
                            self.process_metrics[cid] = {}
                        if pid not in self.process_metrics[cid]:
                            self.process_metrics[cid][pid] = {}
                        if metric_key not in self.process_metrics[cid][pid]:
                            self.process_metrics[cid][pid][metric_key] = Metric(
                                metric_key,
                                proc_measure.type,
                                current=measure.value,
                                capacity=measure.capacity or measure.value,
                                unit_hint=proc_measure.unit_hint,
                                stats=MovingStatistics(measure.value),
                                stats_filter=frozenset(proc_measure.stats_filter),
                                current_hook=proc_measure.current_hook,
                            )
                        else:
                            self.process_metrics[cid][pid][metric_key].update(measure)

            self._stage_observer.observe_stage(
                stage="before_report_to_redis",
                upper_layer="collect_per_container_process_stat",
            )

            # Use ValkeyStatClient set_multiple_keys for batch operations
            key_value_map: dict[str, bytes] = {}
            for cid in updated_cids:
                serializable_table = {}
                for pid in self.process_metrics[cid].keys():
                    metrics = self.process_metrics[cid][pid]
                    serializable_metrics = {}
                    for key, obj in metrics.items():
                        try:
                            serializable_metrics[str(key)] = obj.to_serializable_dict()
                        except ValueError:
                            log.warning("Failed to serialize metric {}: {}", key, str(obj.stats))
                            continue
                    serializable_table[pid] = serializable_metrics
                if self.agent.local_config.debug.log_stats:
                    log.debug(
                        "stats: process_updates: \ncontainer_id: {}\n{}",
                        cid,
                        serializable_table,
                    )
                serialized_metrics = msgpack.packb(serializable_table)
                key_value_map[str(cid)] = serialized_metrics

            if key_value_map:
                await self.agent.valkey_stat_client.set_multiple_keys(key_value_map, expire_sec=8)
