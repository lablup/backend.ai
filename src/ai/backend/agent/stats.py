"""
A module to collect various performance metrics of Docker containers.

Reference: https://www.datadoghq.com/blog/how-to-collect-docker-metrics/
"""

import asyncio
import enum
import logging
import sys
import time
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
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
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.identity import is_containerized
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    PID,
    ContainerId,
    DeviceId,
    KernelId,
    MetricKey,
    MetricValue,
    MovingStatValue,
)

from .utils import remove_exponent

if TYPE_CHECKING:
    from .agent import AbstractAgent

__all__ = (
    "StatContext",
    "StatModes",
    "MetricTypes",
    "NodeMeasurement",
    "ContainerMeasurement",
    "Measurement",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


def check_cgroup_available():
    """
    Check if the host OS provides cgroups.
    """
    return not is_containerized() and sys.platform.startswith("linux")


class StatModes(enum.Enum):
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

    def __init__(self, initial_value: Decimal = None):
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


class StatContext:
    agent: "AbstractAgent"
    mode: StatModes
    node_metrics: dict[MetricKey, Metric]
    device_metrics: dict[MetricKey, dict[DeviceId, Metric]]
    kernel_metrics: dict[KernelId, dict[MetricKey, Metric]]
    process_metrics: dict[ContainerId, dict[PID, dict[MetricKey, Metric]]]

    def __init__(
        self, agent: "AbstractAgent", mode: StatModes = None, *, cache_lifespan: int = 120
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

    async def collect_node_stat(self):
        """
        Collect the per-node, per-device, and per-container statistics.

        Intended to be used by the agent.
        """
        async with self._lock:
            # Here we use asyncio.gather() instead of aiotools.TaskGroup
            # to keep methods of other plugins running when a plugin raises an error
            # instead of cancelling them.
            _tasks: list[asyncio.Task[Sequence[NodeMeasurement]]] = []
            for computer in self.agent.computers.values():
                _tasks.append(asyncio.create_task(computer.instance.gather_node_measures(self)))
            results = await asyncio.gather(*_tasks, return_exceptions=True)
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

        # push to the Redis server
        redis_agent_updates = {
            "node": {key: obj.to_serializable_dict() for key, obj in self.node_metrics.items()},
            "devices": {
                metric_key: {
                    str(dev_id): obj.to_serializable_dict() for dev_id, obj in per_device.items()
                }
                for metric_key, per_device in self.device_metrics.items()
            },
        }
        if self.agent.local_config["debug"]["log-stats"]:
            log.debug(
                "stats: node_updates: {0}: {1}",
                self.agent.local_config["agent"]["id"],
                redis_agent_updates["node"],
            )
        serialized_agent_updates = msgpack.packb(redis_agent_updates)

        async def _pipe_builder(r: Redis):
            pipe = r.pipeline()
            await pipe.set(self.agent.local_config["agent"]["id"], serialized_agent_updates)
            await pipe.expire(self.agent.local_config["agent"]["id"], self.cache_lifespan)
            return pipe

        await redis_helper.execute(self.agent.redis_stat_pool, _pipe_builder)

    async def collect_container_stat(
        self,
        container_ids: Sequence[ContainerId],
    ) -> None:
        """
        Collect the per-container statistics only,

        Intended to be used by the agent and triggered by container cgroup synchronization processes.
        """
        async with self._lock:
            kernel_id_map: Dict[ContainerId, KernelId] = {}
            for kid, info in self.agent.kernel_registry.items():
                try:
                    cid = info["container_id"]
                except KeyError:
                    log.warning("collect_container_stat(): no container for kernel {}", kid)
                else:
                    kernel_id_map[ContainerId(cid)] = kid
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
            results = await asyncio.gather(*_tasks, return_exceptions=True)
            updated_kernel_ids: Set[KernelId] = set()
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

        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline(transaction=False)
            for kernel_id in updated_kernel_ids:
                metrics = self.kernel_metrics[kernel_id]
                serializable_metrics = {
                    str(key): obj.to_serializable_dict() for key, obj in metrics.items()
                }
                if self.agent.local_config["debug"]["log-stats"]:
                    log.debug("kernel_updates: {0}: {1}", kernel_id, serializable_metrics)
                serialized_metrics = msgpack.packb(serializable_metrics)
                pipe.set(str(kernel_id), serialized_metrics)
            return pipe

        await redis_helper.execute(self.agent.redis_stat_pool, _pipe_builder)

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

        async with self._lock:
            pid_map = {}
            pids = []
            async with aiodocker.Docker() as docker:
                for cid in container_ids:
                    try:
                        result = await docker._query_json(f"containers/{cid}/top", method="GET")
                        procs = result["Processes"]
                        pids = [PID(int(proc[1])) for proc in procs]
                        unused_pids = set(self.process_metrics[cid].keys()) - set(pids)
                    except (KeyError, aiodocker.exceptions.DockerError):
                        log.debug(
                            "collect_per_container_process_stat(): cannot found container {}", cid
                        )
                    else:
                        for unused_pid in unused_pids:
                            log.debug("removing pid_metric for {}: {}", cid, unused_pid)
                            self.process_metrics[cid].pop(unused_pid, None)
                    for pid in pids:
                        pid_map[pid] = cid

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
            results = await asyncio.gather(*_tasks, return_exceptions=True)
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

            async def _pipe_builder(r: Redis) -> Pipeline:
                pipe = r.pipeline(transaction=False)
                for cid in updated_cids:
                    serializable_table = {}
                    for pid in self.process_metrics[cid].keys():
                        metrics = self.process_metrics[cid][pid]
                        serializable_metrics = {
                            str(key): obj.to_serializable_dict() for key, obj in metrics.items()
                        }
                        serializable_table[pid] = serializable_metrics
                    if self.agent.local_config["debug"]["log-stats"]:
                        log.debug(
                            "stats: process_updates: \ncontainer_id: {}\n{}",
                            cid,
                            serializable_table,
                        )
                    serialized_metrics = msgpack.packb(serializable_table)
                    pipe.set(cid, serialized_metrics, ex=8)
                return pipe

            await redis_helper.execute(self.agent.redis_stat_pool, _pipe_builder)
