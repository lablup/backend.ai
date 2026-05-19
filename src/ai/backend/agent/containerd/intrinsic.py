"""Intrinsic compute plugins (CPU, main memory) for the containerd backend.

These mirror the docker backend's `CPUPlugin` / `MemoryPlugin` but drop
every Docker-API dependency: device discovery and node statistics are
host-level (psutil / libnuma / sysfs), and container statistics are read
straight from the cgroup filesystem via the agent's `get_cgroup_path()`.
`generate_docker_args()` / `get_docker_networks()` are required by the
abstract base but are no-ops here — the containerd backend builds its OCI
spec and CNI network itself.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
from collections.abc import Collection, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import psutil

from ai.backend.agent import __version__  # pants: no-infer-dep
from ai.backend.agent.alloc_map import AllocationStrategy
from ai.backend.agent.errors import InvalidResourceConfigError
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ai.backend.agent.stats import (
    ContainerMeasurement,
    Measurement,
    MetricTypes,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.agent.utils import read_sysfs
from ai.backend.agent.vendor.linux import libnuma
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    MetricKey,
    SlotName,
    SlotTypes,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Non-device filesystems pruned when summing disk usage.
_PRUNED_DISK_TYPES = frozenset({"vfat", "lxcfs", "squashfs", "tmpfs", "iso9660"})


class CPUDevice(AbstractComputeDevice):
    pass


class CPUPlugin(AbstractComputePlugin):
    """Intrinsic compute plugin representing the host CPU."""

    config_watch_enabled = False

    key = DeviceName("cpu")
    slot_types = [
        (SlotName("cpu"), SlotTypes.COUNT),
    ]

    async def init(self, context: Any | None = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def list_devices(self) -> Collection[CPUDevice]:
        cores = await libnuma.get_available_cores()
        overcommit_factor = int(os.environ.get("BACKEND_CPU_OVERCOMMIT_FACTOR", "1"))
        if not (1 <= overcommit_factor <= 10):
            raise InvalidResourceConfigError(
                f"BACKEND_CPU_OVERCOMMIT_FACTOR must be between 1 and 10, got {overcommit_factor}"
            )
        return [
            CPUDevice(
                device_id=DeviceId(str(core_idx)),
                hw_location="root",
                numa_node=libnuma.node_of_cpu(core_idx),
                memory_size=0,
                processing_units=1 * overcommit_factor,
            )
            for core_idx in sorted(cores)
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("cpu"): Decimal(sum(dev.processing_units for dev in devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {
            "agent_version": __version__,
            "machine": platform.machine(),
            "os_type": platform.system(),
        }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        _cstat = psutil.cpu_times(True)
        q = Decimal("0.000")
        total_cpu_used = cast(
            Decimal, sum((Decimal(c.user + c.system) * 1000).quantize(q) for c in _cstat)
        )
        now, raw_interval = ctx.update_timestamp("cpu-node")
        interval = Decimal(raw_interval * 1000).quantize(q)
        return [
            NodeMeasurement(
                MetricKey("cpu_util"),
                MetricTypes.UTILIZATION,
                unit_hint="msec",
                current_hook=lambda metric: metric.stats.diff,
                per_node=Measurement(total_cpu_used, interval),
                per_device={
                    DeviceId(str(idx)): Measurement(
                        (Decimal(c.user + c.system) * 1000).quantize(q),
                        interval,
                    )
                    for idx, c in enumerate(_cstat)
                },
            ),
        ]

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        if not container_ids:
            return []

        def sysfs_impl(container_id: str) -> float | None:
            cpu_path = ctx.agent.get_cgroup_path("cpuacct", container_id)
            version = ctx.agent.get_cgroup_version()
            try:
                match version:
                    case "1":
                        return read_sysfs(cpu_path / "cpuacct.usage", int) / 1e6
                    case "2":
                        cpu_stats = {
                            k: v
                            for k, v in (
                                line.split(" ")
                                for line in (cpu_path / "cpu.stat").read_text().splitlines()
                            )
                        }
                        return int(cpu_stats["usage_usec"]) / 1e3
                    case _:
                        return None
            except OSError as e:
                log.warning(
                    "CPUPlugin: cannot read cgroup stats for container {0}: {1!r}",
                    container_id[:7],
                    e,
                )
                return None

        q = Decimal("0.000")
        per_container_cpu_used = {}
        per_container_cpu_util = {}
        for cid in container_ids:
            cpu_used = await asyncio.to_thread(sysfs_impl, cid)
            if cpu_used is None:
                continue
            per_container_cpu_used[cid] = Measurement(Decimal(cpu_used).quantize(q))
            per_container_cpu_util[cid] = Measurement(
                Decimal(cpu_used).quantize(q),
                capacity=Decimal(1000),
            )
        return [
            ContainerMeasurement(
                MetricKey("cpu_util"),
                MetricTypes.UTILIZATION,
                unit_hint="percent",
                current_hook=lambda metric: metric.stats.rate,
                stats_filter=frozenset({"avg", "max"}),
                per_container=per_container_cpu_util,
            ),
            ContainerMeasurement(
                MetricKey("cpu_used"),
                MetricTypes.ACCUMULATION,
                unit_hint="msec",
                per_container=per_container_cpu_used,
            ),
        ]

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        q = Decimal("0.000")
        per_process_cpu_util = {}
        per_process_cpu_used = {}
        for pid, cid in pid_map.items():
            try:
                cpu_times = psutil.Process(pid).cpu_times()
            except psutil.NoSuchProcess:
                log.debug("Process not found for CPU stats (pid:{0}, cid:{1})", pid, cid)
                continue
            cpu_used = Decimal(cpu_times.user + cpu_times.system) * 1000
            per_process_cpu_util[pid] = Measurement(cpu_used.quantize(q), capacity=Decimal(1000))
            per_process_cpu_used[pid] = Measurement(cpu_used.quantize(q))
        return [
            ProcessMeasurement(
                MetricKey("cpu_util"),
                MetricTypes.UTILIZATION,
                unit_hint="percent",
                current_hook=lambda metric: metric.stats.rate,
                stats_filter=frozenset({"avg", "max"}),
                per_process=per_process_cpu_util,
            ),
            ProcessMeasurement(
                MetricKey("cpu_used"),
                MetricTypes.ACCUMULATION,
                unit_hint="msec",
                per_process=per_process_cpu_used,
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(
                    SlotTypes.COUNT, SlotName("cpu"), Decimal(dev.processing_units)
                )
                for dev in devices
            },
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(self, docker: Any, device_alloc: Any) -> Mapping[str, Any]:
        # The containerd backend builds its own OCI spec; no docker args.
        return {}

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        # Alloc-map restoration on agent restart is handled by the kernel
        # registry recovery path (a later increment); nothing to do here.
        return

    async def get_attached_devices(self, device_alloc: Any) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("cpu")].keys()]
        available_devices = await self.list_devices()
        return [
            {"device_id": device.device_id, "model_name": "", "data": {"cores": len(device_ids)}}
            for device in available_devices
            if device.device_id in device_ids
        ]

    async def get_docker_networks(self, device_alloc: Any) -> list[str]:
        return []

    async def generate_mounts(self, source_path: Path, device_alloc: Any) -> list[MountInfo]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "cpu",
            "description": "CPU",
            "human_readable_name": "CPU",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "cpu",
        }


class MemoryDevice(AbstractComputeDevice):
    pass


class MemoryPlugin(AbstractComputePlugin):
    """Intrinsic compute plugin representing the host's main memory."""

    config_watch_enabled = False

    key = DeviceName("mem")
    slot_types = [
        (SlotName("mem"), SlotTypes.BYTES),
    ]

    async def init(self, context: Any | None = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def list_devices(self) -> Collection[MemoryDevice]:
        memory_size = psutil.virtual_memory().total
        overcommit_factor = int(os.environ.get("BACKEND_MEM_OVERCOMMIT_FACTOR", "1"))
        return [
            MemoryDevice(
                device_id=DeviceId("root"),
                device_name=self.key,
                hw_location="root",
                numa_node=0,
                memory_size=overcommit_factor * memory_size,
                processing_units=0,
            ),
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("mem"): Decimal(sum(dev.memory_size for dev in devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        _mstat = psutil.virtual_memory()
        total_mem_used_bytes = Decimal(_mstat.total - _mstat.available)
        total_mem_capacity_bytes = Decimal(_mstat.total)
        _nstat = psutil.net_io_counters()
        net_rx_bytes = _nstat.bytes_recv
        net_tx_bytes = _nstat.bytes_sent

        def get_disk_stat() -> tuple[Decimal, Decimal, dict[DeviceId, Measurement]]:
            total_disk_usage = Decimal(0)
            total_disk_capacity = Decimal(0)
            per_disk_stat: dict[DeviceId, Measurement] = {}
            for disk_info in psutil.disk_partitions():
                if disk_info.fstype in _PRUNED_DISK_TYPES:
                    continue
                dstat = os.statvfs(disk_info.mountpoint)
                disk_usage = Decimal(dstat.f_frsize * (dstat.f_blocks - dstat.f_bavail))
                disk_capacity = Decimal(dstat.f_frsize * dstat.f_blocks)
                per_disk_stat[DeviceId(disk_info.device)] = Measurement(disk_usage, disk_capacity)
                total_disk_usage += disk_usage
                total_disk_capacity += disk_capacity
            return total_disk_usage, total_disk_capacity, per_disk_stat

        total_disk_usage, total_disk_capacity, per_disk_stat = await asyncio.to_thread(
            get_disk_stat
        )
        return [
            NodeMeasurement(
                MetricKey("mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(total_mem_used_bytes, total_mem_capacity_bytes),
                per_device={
                    DeviceId("root"): Measurement(total_mem_used_bytes, total_mem_capacity_bytes)
                },
            ),
            NodeMeasurement(
                MetricKey("disk"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                per_node=Measurement(total_disk_usage, total_disk_capacity),
                per_device=per_disk_stat,
            ),
            NodeMeasurement(
                MetricKey("net_rx"),
                MetricTypes.RATE,
                unit_hint="bps",
                current_hook=lambda metric: metric.stats.rate,
                per_node=Measurement(Decimal(net_rx_bytes)),
                per_device={DeviceId("node"): Measurement(Decimal(net_rx_bytes))},
            ),
            NodeMeasurement(
                MetricKey("net_tx"),
                MetricTypes.RATE,
                unit_hint="bps",
                current_hook=lambda metric: metric.stats.rate,
                per_node=Measurement(Decimal(net_tx_bytes)),
                per_device={DeviceId("node"): Measurement(Decimal(net_tx_bytes))},
            ),
        ]

    async def gather_container_measures(
        self, ctx: StatContext, container_ids: Sequence[str]
    ) -> Sequence[ContainerMeasurement]:
        if not container_ids:
            return []

        def sysfs_impl(container_id: str) -> tuple[int, int, int, int] | None:
            mem_path = ctx.agent.get_cgroup_path("memory", container_id)
            io_path = ctx.agent.get_cgroup_path("blkio", container_id)
            version = ctx.agent.get_cgroup_version()
            io_read_bytes = 0
            io_write_bytes = 0
            try:
                match version:
                    case "1":
                        mem_cur_bytes = read_sysfs(mem_path / "memory.usage_in_bytes", int)
                        mem_max_bytes = read_sysfs(mem_path / "memory.limit_in_bytes", int)
                        for line in (
                            (io_path / "blkio.throttle.io_service_bytes").read_text().splitlines()
                        ):
                            if line.startswith("Total "):
                                continue
                            _dev, op, nbytes = line.strip().split()
                            if op == "Read":
                                io_read_bytes += int(nbytes)
                            elif op == "Write":
                                io_write_bytes += int(nbytes)
                    case "2":
                        mem_cur_bytes = read_sysfs(mem_path / "memory.current", int)
                        mem_max_bytes = read_sysfs(mem_path / "memory.max", int)
                        for line in (io_path / "io.stat").read_text().splitlines():
                            for io_stat in line.split():
                                stat, _, value = io_stat.partition("=")
                                if stat == "rbytes":
                                    io_read_bytes += int(value)
                                elif stat == "wbytes":
                                    io_write_bytes += int(value)
                    case _:
                        return None
            except OSError as e:
                log.warning(
                    "MemoryPlugin: cannot read cgroup stats for container {0}: {1!r}",
                    container_id[:7],
                    e,
                )
                return None
            return mem_cur_bytes, mem_max_bytes, io_read_bytes, io_write_bytes

        per_container_mem_used_bytes = {}
        per_container_io_read_bytes = {}
        per_container_io_write_bytes = {}
        for cid in container_ids:
            result = await asyncio.to_thread(sysfs_impl, cid)
            if result is None:
                continue
            mem_cur, mem_max, io_read, io_write = result
            per_container_mem_used_bytes[cid] = Measurement(
                Decimal(mem_cur), capacity=Decimal(mem_max)
            )
            per_container_io_read_bytes[cid] = Measurement(Decimal(io_read))
            per_container_io_write_bytes[cid] = Measurement(Decimal(io_write))
        return [
            ContainerMeasurement(
                MetricKey("mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_container=per_container_mem_used_bytes,
            ),
            ContainerMeasurement(
                MetricKey("io_read"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_container=per_container_io_read_bytes,
            ),
            ContainerMeasurement(
                MetricKey("io_write"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_container=per_container_io_write_bytes,
            ),
        ]

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        per_process_mem_used_bytes = {}
        per_process_io_read_bytes = {}
        per_process_io_write_bytes = {}
        for pid, cid in pid_map.items():
            try:
                stats = psutil.Process(pid).as_dict(attrs=["memory_info", "io_counters"])
            except psutil.NoSuchProcess:
                log.debug("Process not found for memory stats (pid:{0}, cid:{1})", pid, cid)
                continue
            if stats["memory_info"] is not None:
                per_process_mem_used_bytes[pid] = Measurement(Decimal(stats["memory_info"].rss))
            if stats["io_counters"] is not None:
                per_process_io_read_bytes[pid] = Measurement(
                    Decimal(stats["io_counters"].read_bytes)
                )
                per_process_io_write_bytes[pid] = Measurement(
                    Decimal(stats["io_counters"].write_bytes)
                )
        return [
            ProcessMeasurement(
                MetricKey("mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_process=per_process_mem_used_bytes,
            ),
            ProcessMeasurement(
                MetricKey("io_read"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_process=per_process_io_read_bytes,
            ),
            ProcessMeasurement(
                MetricKey("io_write"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_process=per_process_io_write_bytes,
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            allocation_strategy=AllocationStrategy.FILL,
            device_slots={
                dev.device_id: DeviceSlotInfo(
                    SlotTypes.BYTES, SlotName("mem"), Decimal(dev.memory_size)
                )
                for dev in devices
            },
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(self, docker: Any, device_alloc: Any) -> Mapping[str, Any]:
        # The containerd backend builds its own OCI spec; no docker args.
        return {}

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        # See CPUPlugin.restore_from_container.
        return

    async def get_attached_devices(self, device_alloc: Any) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("mem")].keys()]
        available_devices = await self.list_devices()
        return [
            {"device_id": device.device_id, "model_name": "", "data": {}}
            for device in available_devices
            if device.device_id in device_ids
        ]

    async def get_docker_networks(self, device_alloc: Any) -> list[str]:
        return []

    async def generate_mounts(self, source_path: Path, device_alloc: Any) -> list[MountInfo]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "ram",
            "description": "Memory",
            "human_readable_name": "RAM",
            "display_unit": "GiB",
            "number_format": {"binary": True, "round_length": 0},
            "display_icon": "ram",
        }
