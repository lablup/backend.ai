import asyncio
import glob
import logging
import re
from collections.abc import Mapping, MutableMapping, Sequence
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import Any

import aiodocker

from ai.backend.accelerator.furiosa import __version__

from .rngd_api import LibraryError, RngdAPI

try:
    from ai.backend.agent.resources import get_resource_spec_from_container  # type: ignore
except ImportError:
    from ai.backend.agent.docker.resources import get_resource_spec_from_container

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
    MetricKey,
    MetricTypes,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AcceleratorMetadata,
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)

PREFIX = "rngd"
_NPU_INDEX_RE = re.compile(r"/dev/rngd/npu(\d+)")


log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.rngd"))


class RngdDevice(AbstractComputeDevice):
    model_name: str
    serial: str

    def __init__(self, model_name: str, serial: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.serial = serial

    def __str__(self) -> str:
        return f"Furiosa {self.model_name} <{self.hw_location}, Memory {self.memory_size}, NUMA Node #{self.numa_node}>"

    def __repr__(self) -> str:
        return self.__str__()


class RngdPlugin(AbstractComputePlugin):
    key = DeviceName("rngd")
    slot_types: Sequence[tuple[SlotName, SlotTypes]] = (
        (SlotName("rngd.device"), SlotTypes("count")),
    )
    exclusive_slot_types: set[str] = {"rngd.device"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True
    rngd_config: Any

    _rbln_stat_path: str
    _all_devices: list[RngdDevice] | None

    async def init(self, context: Any = None) -> None:
        self._all_devices = None

        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]

        try:
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            log.info("RNGD acceleration is enabled.")
        except ImportError:
            log.warning("could not find Furiosa devices.")
            self.enabled = False

    async def list_devices(self) -> list[RngdDevice]:
        if self._all_devices is not None:
            return self._all_devices
        devices: list[RngdDevice] = []
        for device_info in await RngdAPI.list_devices():
            devices.append(
                RngdDevice(
                    model_name=device_info.arch,
                    serial=device_info.device_serial,
                    device_id=str(device_info.device_index),
                    hw_location=device_info.pci_bus_id,
                    memory_size=device_info.memory_size,
                    processing_units=device_info.num_cores,
                    numa_node=device_info.numa_node,
                )
            )

        self._all_devices = devices
        return devices

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("rngd.device"): Decimal(len(devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            return {
                "rngd_support": True,
            }
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        dev_count = 0
        mem_total_agg = 0
        mem_used_agg = 0
        mem_stats: dict[DeviceId, Measurement] = {}
        util_total = 0.0
        util_stats: dict[DeviceId, Measurement] = {}
        if self.enabled:
            try:
                for device in await self.list_devices():
                    if device.device_id in self.device_mask:
                        continue
                    dev_count += 1
                    metrics = await RngdAPI.get_device_metrics(int(device.device_id))
                    mem_total_agg += metrics.memory_total
                    mem_used_agg += metrics.memory_used
                    mem_stats[device.device_id] = Measurement(
                        Decimal(metrics.memory_used), Decimal(metrics.memory_total)
                    )
                    avg_util = (
                        sum(metrics.core_utilizations) / len(metrics.core_utilizations)
                        if metrics.core_utilizations
                        else 0.0
                    )
                    util_total += avg_util
                    util_stats[device.device_id] = Measurement(Decimal(avg_util), Decimal(100))
            except (LibraryError, OSError) as e:
                log.warning("failed to gather RNGD node measures: {}", e)
        return [
            NodeMeasurement(
                MetricKey("rngd_mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_agg), Decimal(mem_total_agg)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey("rngd_util"),
                MetricTypes.UTILIZATION,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_node=Measurement(Decimal(util_total), Decimal(dev_count * 100)),
                per_device=util_stats,
            ),
        ]

    async def gather_container_measures(
        self, ctx: StatContext, container_ids: Sequence[str]
    ) -> Sequence[ContainerMeasurement]:
        mem_stats: dict[str, int] = {}
        mem_sizes: dict[str, int] = {}
        util_stats: dict[str, Decimal] = {}
        num_devices_per_container: dict[str, int] = {}

        if not self.enabled:
            return []

        # Step 1: Collect per-device metrics
        device_metrics: dict[int, tuple[int, int, float]] = {}  # idx -> (used, total, util%)
        try:
            for device in await self.list_devices():
                if device.device_id in self.device_mask:
                    continue
                dev_idx = int(device.device_id)
                metrics = await RngdAPI.get_device_metrics(dev_idx)
                avg_util = (
                    sum(metrics.core_utilizations) / len(metrics.core_utilizations)
                    if metrics.core_utilizations
                    else 0.0
                )
                device_metrics[dev_idx] = (
                    metrics.memory_used,
                    metrics.memory_total,
                    avg_util,
                )
        except (LibraryError, OSError) as e:
            log.warning("failed to gather RNGD device metrics: {}", e)
            return []

        # Step 2: For each container, find allocated devices via Docker inspection
        for cid in container_ids:
            mem_stats[cid] = 0
            mem_sizes[cid] = 0
            util_stats[cid] = Decimal("0")
            num_devices_per_container[cid] = 0
            try:
                async with aiodocker.Docker() as docker:
                    container_info = await docker.containers.get(cid)
                seen_indices: set[int] = set()
                for dev_entry in container_info["HostConfig"].get("Devices", []):
                    m = _NPU_INDEX_RE.match(dev_entry["PathOnHost"])
                    if m is None:
                        continue
                    dev_idx = int(m.group(1))
                    if dev_idx in seen_indices:
                        continue
                    seen_indices.add(dev_idx)
                    dev_metric = device_metrics.get(dev_idx)
                    if dev_metric is None:
                        continue
                    mem_used, mem_total, avg_util = dev_metric
                    mem_stats[cid] += mem_used
                    mem_sizes[cid] += mem_total
                    util_stats[cid] += Decimal(str(avg_util))
                    num_devices_per_container[cid] += 1
            except Exception:
                log.warning("failed to inspect container {} for RNGD measures", cid)

        return [
            ContainerMeasurement(
                MetricKey("rngd_mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_container={
                    cid: Measurement(Decimal(usage), Decimal(mem_sizes[cid]))
                    for cid, usage in mem_stats.items()
                },
            ),
            ContainerMeasurement(
                MetricKey("rngd_util"),
                MetricTypes.UTILIZATION,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_container={
                    cid: Measurement(util, Decimal(num_devices_per_container[cid] * 100))
                    for cid, util in util_stats.items()
                },
            ),
        ]

    async def create_alloc_map(self) -> DiscretePropertyAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: (
                    DeviceSlotInfo(SlotTypes.COUNT, SlotName("rngd.device"), Decimal(1))
                )
                for dev in devices
            },
            exclusive_slot_types=self.exclusive_slot_types,
        )

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[MountInfo]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        device_ids = [
            x.device_id
            for x in await self.list_devices()
            if x.device_id in device_alloc.get(SlotName("rngd.device"), {}).keys()
        ]
        devices: dict[str, str] = {}
        for alloc_idx, device_id in enumerate(device_ids):
            source_paths = await asyncio.get_running_loop().run_in_executor(
                None, glob.glob, f"/dev/rngd/npu{device_id}*"
            )
            for source_path in source_paths:
                devices[str(source_path)] = str(source_path).replace(
                    f"npu{device_id}", f"npu{alloc_idx}"
                )

        return {
            "HostConfig": {
                "CapAdd": ["IPC_LOCK"],
                "SecurityOpt": ["seccomp=unconfined"],
                "IpcMode": "host",
                "Ulimits": [{"Name": "memlock", "Hard": -1, "Soft": -1}],
                "Sysctls": {"net.ipv6.conf.all.disable_ipv6": "0"},
                "Devices": [
                    {
                        "PathOnHost": host_path,
                        "PathInContainer": container_path,
                        "CgroupPermissions": "rwm",
                    }
                    for host_path, container_path in devices.items()
                ],
            }
        }

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: list[DeviceId] = []
        if SlotName("rngd.device") in device_alloc:
            device_ids.extend(device_alloc[SlotName("rngd.device")].keys())
        available_devices = await self.list_devices()
        attached_devices: list[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                proc = device.processing_units
                mem = BinarySize(device.memory_size)
                attached_devices.append({  # TODO: update common.types.DeviceModelInfo
                    "device_id": device.device_id,
                    "model_name": device.model_name,
                    "data": {
                        "proc": proc,
                        "mem": mem,
                    },
                })
        return attached_devices

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        if not self.enabled:
            return
        resource_spec = await get_resource_spec_from_container(container.backend_obj)
        if resource_spec is None:
            return
        if hasattr(alloc_map, "apply_allocation"):
            for slot_name, _ in self.slot_types:
                alloc_map.apply_allocation({
                    slot_name: resource_spec.allocations.get(
                        DeviceName("rngd"),
                        {},
                    ).get(
                        slot_name,
                        {
                            dev_id: Decimal(0)
                            for dev_id, dev_slot_info in alloc_map.device_slots.items()
                            if dev_slot_info.slot_name == slot_name
                        },
                    ),
                })
        else:  # older agents without lablup/backend.ai-agent#180
            alloc_map.allocations[SlotName("rngd.device")].update(
                resource_spec.allocations.get(
                    DeviceName("rngd"),
                    {},
                ).get(
                    SlotName("rngd.device"),
                    {},
                ),
            )

    async def generate_resource_data(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, str]:
        data: MutableMapping[str, str] = {}
        if not self.enabled:
            return data

        active_device_id_set: set[DeviceId] = set()
        for slot_type, per_device_alloc in device_alloc.items():
            for dev_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    active_device_id_set.add(dev_id)
        active_device_ids = sorted(active_device_id_set, key=lambda v: int(v))
        data["FURIOSA_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "rngd.device",
            "description": "RNGD",
            "human_readable_name": "Furiosa RNGD Device",
            "display_unit": "NPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "npu3",
        }
