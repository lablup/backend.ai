import logging
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Collection,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import aiodocker

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)

from . import __version__
from .exception import (
    GenericRocmError,
    NoRocmDeviceError,
    RocmMemFetchError,
    RocmUtilFetchError,
)
from .hip import libhip, librocm_smi
from .types import ROCmDevice, ROCmXCD

try:
    from ai.backend.agent.resources import get_resource_spec_from_container  # type: ignore
except ImportError:
    from ai.backend.agent.docker.resources import get_resource_spec_from_container
from ai.backend.agent.stats import (
    ContainerMeasurement,
    Measurement,
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
    MetricKey,
    SlotName,
    SlotTypes,
)

__all__ = (
    "PREFIX",
    "ROCmDevice",
    "ROCmPlugin",
)

PREFIX = "rocm"

log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.rocm"))


class ROCmPlugin(AbstractComputePlugin):
    config_watch_enabled = False

    key = DeviceName("rocm")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("rocm.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"rocm.device"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True

    _all_devices: Optional[List[ROCmDevice]]

    async def init(self, context: Any = None) -> None:
        self._all_devices = None

        raw_device_mask = self.local_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]
        try:
            librocm_smi.init()
            (major, minor, patch) = librocm_smi.get_version()
            if major < 6:
                raise RuntimeError("Unsupported ROCm version {}.{}.{}", major, minor, patch)
            log.info("Running on ROCm {}.{}.{}", major, minor, patch)
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            libhip.get_device_count()
            log.info("ROCm acceleration is enabled.")
        except (ImportError, NoRocmDeviceError, GenericRocmError):
            log.warning("could not load the ROCm HIP library.")
            log.info("ROCm acceleration is disabled.")
            self.enabled = False
        except RuntimeError as e:
            log.warning("ROCm init error: {}", e)
            log.info("ROCm acceleration is disabled.")
            self.enabled = False

    async def list_devices(self) -> Collection[ROCmDevice]:
        if not self.enabled:
            return []

        if self._all_devices is not None:
            return self._all_devices

        num_devices = libhip.get_device_count()

        devices_by_serial: Dict[str, ROCmDevice] = {}

        for dev_id in range(num_devices):
            if dev_id in self.device_mask:
                continue
            # Use HIP only for fetching multiProcessorCount
            raw_info = libhip.get_device_props(int(dev_id))
            pci_bus_id = raw_info["pciBusID_str"]
            sysfs_node_path = f"/sys/bus/pci/devices/{pci_bus_id}/numa_node"
            node: Optional[int]
            try:
                node = int(Path(sysfs_node_path).read_text().strip())
            except OSError:
                node = None
            (_, minor, _) = librocm_smi.get_version()
            if minor == 1:
                unique_id = librocm_smi.get_serial_number(dev_id)
            else:
                unique_id = librocm_smi.get_gpu_uuid(dev_id)[2:]
            serial = librocm_smi.get_serial_number(dev_id)
            sku = librocm_smi.get_gpu_sku(dev_id)

            if serial in devices_by_serial:
                dev_info = devices_by_serial[serial]
                dev_info.xcds.append(
                    ROCmXCD(
                        DeviceId(str(dev_id)),
                        pci_bus_id,
                        raw_info["totalGlobalMem"],
                        raw_info["multiProcessorCount"],
                        numa_node=node,
                    )
                )
                dev_info.memory_size += raw_info["totalGlobalMem"]
                dev_info.processing_units += raw_info["multiProcessorCount"]
            else:
                dev_info = ROCmDevice(
                    device_id=DeviceId(serial),
                    hw_location=pci_bus_id,
                    numa_node=node,
                    xcds=[
                        ROCmXCD(
                            DeviceId(str(dev_id)),
                            pci_bus_id,
                            raw_info["totalGlobalMem"],
                            raw_info["multiProcessorCount"],
                            numa_node=node,
                        )
                    ],
                    memory_size=raw_info["totalGlobalMem"],
                    # TODO: Find way to fetch multiProcessorCount without using HIP
                    processing_units=raw_info["multiProcessorCount"],
                    model_name=raw_info["name"],
                    unique_id=unique_id,
                    sku=sku,
                )
                devices_by_serial[serial] = dev_info

        self._all_devices = [d for d in devices_by_serial.values()]
        return self._all_devices

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("rocm.device"): Decimal(len(devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            try:
                return {
                    "rocm_support": True,
                    "driver_version": libhip.get_driver_version(),
                }
            except (GenericRocmError, ImportError):
                self.enabled = False
        return {
            "rocm_support": False,
        }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        dev_count = 0
        mem_avail_total = 0
        mem_used_total = 0
        mem_stats = {}
        util_total = 0
        util_stats = {}
        if self.enabled:
            try:
                for device in await self.list_devices():
                    if device.device_id in self.device_mask:
                        continue

                    for xcd in device.xcds:
                        dev_idx = int(xcd.device_id)
                        mem_used, mem_total = librocm_smi.get_memory_info(dev_idx)
                        gpu_util = librocm_smi.get_gpu_utilization(dev_idx)

                        mem_avail_total += int(mem_total)
                        mem_used_total += int(mem_used)
                        mem_stats[device.device_id] = Measurement(
                            Decimal(mem_used), Decimal(mem_total)
                        )
                        util_total += gpu_util
                        util_stats[device.device_id] = Measurement(Decimal(gpu_util), Decimal(100))

            except (RocmUtilFetchError, RocmMemFetchError) as e:
                # libhip is not installed.
                # Return an empty result.
                log.exception(e)
                self.enabled = False
        return [
            NodeMeasurement(
                MetricKey("rocm_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey("rocm_util"),
                MetricTypes.USAGE,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_node=Measurement(Decimal(util_total), Decimal(dev_count * 100)),
                per_device=util_stats,
            ),
        ]

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        mem_stats: Dict[str, int] = {}
        mem_sizes: Dict[str, int] = {}
        util_stats: Dict[str, Decimal] = {}
        number_of_devices_per_container: Dict[str, int] = {}
        device_stats_by_device_filename: Dict[str, Dict[str, Any]] = {}
        if self.enabled:
            try:
                for device in await self.list_devices():
                    if device.device_id in self.device_mask:
                        continue

                    for xcd in device.xcds:
                        dev_idx = int(xcd.device_id)
                        mem_used, mem_total = librocm_smi.get_memory_info(dev_idx)
                        gpu_util = librocm_smi.get_gpu_utilization(dev_idx)

                        device_stats_by_device_filename[f"/dev/dri/renderD{128 + dev_idx}"] = {
                            "util": gpu_util,
                            "mem_used": mem_used,
                            "mem_total": mem_total,
                        }
            except (RocmUtilFetchError, RocmMemFetchError) as e:
                # libhip is not installed.
                # Return an empty result.
                log.exception(e)
                self.enabled = False
                return []

            log.debug("device_stats_by_device_filename: {}", device_stats_by_device_filename)
            for cid in container_ids:
                mem_stats[cid] = 0
                mem_sizes[cid] = 0
                util_stats[cid] = Decimal("0")
                number_of_devices_per_container[cid] = 0
                async with aiodocker.Docker() as docker:
                    container_info = await docker.containers.get(cid)
                log.debug("Container {}: Devices: {}", cid, container_info["HostConfig"]["Devices"])
                for device in container_info["HostConfig"]["Devices"]:
                    if device["PathOnHost"] in device_stats_by_device_filename:
                        device_stat = device_stats_by_device_filename[device["PathOnHost"]]
                        mem_stats[cid] += int(device_stat["mem_used"])
                        mem_sizes[cid] += int(device_stat["mem_total"])
                        util_stats[cid] += Decimal(device_stat["util"])
                        number_of_devices_per_container[cid] += 1

        return [
            ContainerMeasurement(
                MetricKey("rocm_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_container={
                    cid: Measurement(
                        Decimal(usage),
                        Decimal(mem_sizes[cid]),
                    )
                    for cid, usage in mem_stats.items()
                },
            ),
            ContainerMeasurement(
                MetricKey("rocm_util"),
                MetricTypes.USAGE,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_container={
                    cid: Measurement(
                        util,
                        Decimal(number_of_devices_per_container[cid] * 100),
                    )
                    for cid, util in util_stats.items()
                },
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, SlotName("rocm.device"), Decimal(1))
                for dev in devices
            },
            exclusive_slot_types=self.exclusive_slot_types,
        )

    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[MountInfo]:
        return []

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        assigned_xcds: List[ROCmXCD] = []
        for dev in await self.list_devices():
            if dev.device_id in device_alloc.get(self.slot_types[0][0], {}).keys():
                assigned_xcds.extend(dev.xcds)

        if len(assigned_xcds) == 0:
            return {}

        return {
            "HostConfig": {
                "Devices": [
                    *[
                        {
                            "PathOnHost": f"/dev/dri/renderD{128 + int(xcd.device_id)}",
                            "PathInContainer": f"/dev/dri/renderD{128 + int(xcd.device_id)}",
                            "CgroupPermissions": "mrw",
                        }
                        for xcd in assigned_xcds
                    ],
                    {
                        "PathOnHost": "/dev/kfd",
                        "PathInContainer": "/dev/kfd",
                        "CgroupPermissions": "mrw",
                    },
                ],
                # "Privileged": True,
                "SecurityOpt": ["seccomp=unconfined"],
                "GroupAdd": ["video", "render"],
            },
        }

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: List[DeviceId] = []
        if SlotName("rocm.device") in device_alloc:
            device_ids.extend(device_alloc[SlotName("rocm.device")].keys())
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                proc = device.processing_units
                mem = BinarySize(device.memory_size)
                attached_devices.append({  # TODO: update common.types.DeviceModelInfo
                    "device_id": device.device_id,
                    "model_name": device.model_name,
                    "data": {
                        "smp": proc,
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
                        DeviceName("rocm"),
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
            alloc_map.allocations[SlotName("rocm.device")].update(
                resource_spec.allocations.get(
                    DeviceName("rocm"),
                    {},
                ).get(
                    SlotName("rocm.device"),
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

        active_device_id_set: Set[DeviceId] = set()
        for slot_type, per_device_alloc in device_alloc.items():
            for dev_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    active_device_id_set.add(dev_id)
        active_device_ids = sorted(active_device_id_set, key=lambda v: int(v))
        data["ROCm_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

    async def cleanup(self) -> None:
        librocm_smi.shutdown()

    async def list_additional_gids(self) -> List[int]:
        return [44, 109]

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def get_docker_networks(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[str]:
        return []

    async def gather_process_measures(
        self,
        ctx: StatContext,
        pid_map: Mapping[int, str],
    ) -> Sequence[ProcessMeasurement]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "rocm.device",
            "description": "ROCm",
            "human_readable_name": "ROCm Device",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "gpu2",
        }
