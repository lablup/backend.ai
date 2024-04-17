import asyncio
import os
from decimal import Decimal
from pathlib import Path
from typing import Any, Collection, Mapping, Sequence, cast

import aiodocker
import psutil

from ai.backend.agent.types import MountInfo
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)

from .. import __version__
from ..alloc_map import AllocationStrategy
from ..resources import (
    AbstractAllocMap,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ..stats import (
    ContainerMeasurement,
    Measurement,
    MetricKey,
    MetricTypes,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from .agent import Container
from .compute_plugin import DummyComputePlugin, DummyDevice
from .config import Intrinsic as IntrinsicConfig


class CPUDevice(DummyDevice):
    pass


class CPUPlugin(DummyComputePlugin):
    """
    Represents the CPU.
    """

    resource_config: IntrinsicConfig

    config_watch_enabled = False

    key = DeviceName("cpu")
    slot_types = [
        (SlotName("cpu"), SlotTypes.COUNT),
    ]

    def __init__(
        self,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
    ) -> None:
        self.resource_config = cast(IntrinsicConfig, local_config["dummy"].agent.intrinsic)

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "cpu",
            "description": "CPU",
            "human_readable_name": "CPU",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "cpu",
        }

    async def list_devices(self) -> Collection[CPUDevice]:
        cores = self.resource_config.cpu_core_indexes
        return [
            CPUDevice(
                model_name=None,
                mother_uuid=None,
                slot_type=SlotTypes.COUNT,
                device_id=DeviceId(str(core_idx)),
                hw_location="root",
                numa_node=None,
                memory_size=0,
                processing_units=1,
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
        return {}

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
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    async def create_alloc_map(self) -> "AbstractAllocMap":
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

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc,
    ) -> Mapping[str, Any]:
        cores = [*map(int, device_alloc["cpu"].keys())]
        sorted_core_ids = [*map(str, sorted(cores))]
        return {
            "HostConfig": {
                "CpuPeriod": 100_000,  # docker default
                "CpuQuota": int(100_000 * len(cores)),
                "Cpus": ",".join(sorted_core_ids),
                "CpusetCpus": ",".join(sorted_core_ids),
                # 'CpusetMems': f'{resource_spec.numa_node}',
            },
        }

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        return None

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("cpu")].keys()]
        available_devices = await self.list_devices()
        attached_devices: list[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": "",
                    "data": {"cores": len(device_ids)},
                })
        return attached_devices

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[MountInfo]:
        return []


class MemoryDevice(DummyDevice):
    pass


class MemoryPlugin(DummyComputePlugin):
    """
    Represents the main memory.
    """

    resource_config: IntrinsicConfig

    config_watch_enabled = False

    key = DeviceName("mem")
    slot_types = [
        (SlotName("mem"), SlotTypes.BYTES),
    ]

    def __init__(
        self,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
    ) -> None:
        self.resource_config = cast(IntrinsicConfig, local_config["dummy"].agent.intrinsic)

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "ram",
            "description": "Memory",
            "human_readable_name": "RAM",
            "display_unit": "GiB",
            "number_format": {"binary": True, "round_length": 0},
            "display_icon": "cpu",
        }

    async def list_devices(self) -> Collection[MemoryDevice]:
        memory_size = self.resource_config.memory_size
        return [
            MemoryDevice(
                model_name=None,
                mother_uuid=None,
                slot_type=SlotTypes.BYTES,
                device_id=DeviceId("root"),
                device_name=self.key,
                hw_location="root",
                numa_node=0,  # the kernel setting will do the job.
                memory_size=memory_size,
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

        def get_disk_stat():
            pruned_disk_types = frozenset(["squashfs", "vfat", "tmpfs"])
            total_disk_usage = Decimal(0)
            total_disk_capacity = Decimal(0)
            per_disk_stat = {}
            for disk_info in psutil.disk_partitions():
                if disk_info.fstype not in pruned_disk_types:
                    if "/var/lib/docker/btrfs" == disk_info.mountpoint:
                        continue
                    dstat = os.statvfs(disk_info.mountpoint)
                    disk_usage = Decimal(dstat.f_frsize * (dstat.f_blocks - dstat.f_bavail))
                    disk_capacity = Decimal(dstat.f_frsize * dstat.f_blocks)
                    per_disk_stat[disk_info.device] = Measurement(disk_usage, disk_capacity)
                    total_disk_usage += disk_usage
                    total_disk_capacity += disk_capacity
            return total_disk_usage, total_disk_capacity, per_disk_stat

        loop = asyncio.get_running_loop()
        total_disk_usage, total_disk_capacity, per_disk_stat = await loop.run_in_executor(
            None, get_disk_stat
        )
        return [
            NodeMeasurement(
                MetricKey("mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(total_mem_used_bytes, total_mem_capacity_bytes),
                per_device={
                    DeviceId("root"): Measurement(total_mem_used_bytes, total_mem_capacity_bytes)
                },
            ),
            NodeMeasurement(
                MetricKey("disk"),
                MetricTypes.USAGE,
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
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    async def create_alloc_map(self) -> "AbstractAllocMap":
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

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc,
    ) -> Mapping[str, Any]:
        return {}

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        return None

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("mem")].keys()]
        available_devices = await self.list_devices()
        attached_devices: list[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": "",
                    "data": {},
                })
        return attached_devices

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[MountInfo]:
        return []
