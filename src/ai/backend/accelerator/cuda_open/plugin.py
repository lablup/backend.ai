import logging
import re
import uuid
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
from aiodocker.exceptions import DockerError
from aiotools import closing_async

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ai.backend.agent.utils import update_nested_dict
from ai.backend.common.logging import BraceStyleAdapter

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

from . import __version__
from .nvidia import LibraryError, libcudart, libnvml

__all__ = (
    "PREFIX",
    "CUDADevice",
    "CUDAPlugin",
)

PREFIX = "cuda"

log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.cuda"))


class CUDADevice(AbstractComputeDevice):
    model_name: str
    uuid: str

    def __init__(self, model_name: str, uuid: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.uuid = uuid

    def __str__(self) -> str:
        return (
            "CUDADevice("
            f"device_id: {self.uuid}, model_name: {self.model_name}, "
            f"processing_unit: {self.processing_units}, memory_size: {self.memory_size}, "
            f"numa_node: {self.numa_node}, hw_location: {self.hw_location}"
            ")"
        )

    def __repr__(self) -> str:
        return str(self)


class CUDAPlugin(AbstractComputePlugin):
    config_watch_enabled = False

    key = DeviceName("cuda")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("cuda.device"), SlotTypes("count")),
    )

    docker_version: Tuple[int, ...] = (0, 0, 0)

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True

    async def init(self, context: Any = None) -> None:
        rx_triple_version = re.compile(r"(\d+\.\d+\.\d+)")

        # Basic docker version & nvidia container runtime check
        try:
            async with closing_async(aiodocker.Docker()) as docker:
                docker_info = await docker.system.info()
        except DockerError:
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
            return

        if "nvidia" not in docker_info["Runtimes"]:
            log.error("could not detect valid NVIDIA Container Runtime!")
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
            return

        rx_triple_version = re.compile(r"(\d+\.\d+\.\d+)")
        m = rx_triple_version.search(docker_info["ServerVersion"])
        if m:
            self.docker_version = tuple(map(int, m.group(1).split(".")))
        else:
            log.error("could not detect docker version!")
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
            return

        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]
        try:
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            log.info("CUDA acceleration is enabled.")
        except ImportError:
            log.warning("could not load the CUDA runtime library.")
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
        except RuntimeError as e:
            log.warning("CUDA init error: {}", e)
            log.info("CUDA acceleration is disabled.")
            self.enabled = False

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(
        self,
        new_plugin_config: Mapping[str, Any],
    ) -> None:
        pass

    async def list_devices(self) -> Collection[CUDADevice]:
        if not self.enabled:
            return []
        all_devices = []
        num_devices = libcudart.get_device_count()
        for dev_id in map(lambda idx: DeviceId(str(idx)), range(num_devices)):
            if dev_id in self.device_mask:
                continue
            raw_info = libcudart.get_device_props(int(dev_id))
            sysfs_node_path = f"/sys/bus/pci/devices/{raw_info['pciBusID_str'].lower()}/numa_node"
            node: Optional[int]
            try:
                node = int(Path(sysfs_node_path).read_text().strip())
            except OSError:
                node = None
            dev_uuid, raw_dev_uuid = None, raw_info.get("uuid", None)
            if raw_dev_uuid is not None:
                dev_uuid = str(uuid.UUID(bytes=raw_dev_uuid))
            else:
                dev_uuid = "00000000-0000-0000-0000-000000000000"
            dev_info = CUDADevice(
                device_id=DeviceId(dev_id),
                hw_location=raw_info["pciBusID_str"],
                numa_node=node,
                memory_size=raw_info["totalGlobalMem"],
                processing_units=raw_info["multiProcessorCount"],
                model_name=raw_info["name"],
                uuid=dev_uuid,
            )
            all_devices.append(dev_info)
        return all_devices

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("cuda.device"): Decimal(len(devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            try:
                return {
                    "cuda_support": True,
                    "nvidia_version": libnvml.get_driver_version(),
                    "cuda_version": "{0[0]}.{0[1]}".format(libcudart.get_version()),
                }
            except ImportError:
                log.warning("extra_info(): NVML/CUDA runtime library is not found")
            except LibraryError as e:
                log.warning("extra_info(): {!r}", e)
        return {
            "cuda_support": False,
        }

    async def gather_node_measures(
        self,
        ctx: StatContext,
    ) -> Sequence[NodeMeasurement]:
        dev_count = 0
        mem_avail_total = 0
        mem_used_total = 0
        mem_stats = {}
        util_total = 0
        util_stats = {}
        if self.enabled:
            try:
                dev_count = libnvml.get_device_count()
                for dev_id in map(lambda idx: DeviceId(str(idx)), range(dev_count)):
                    if dev_id in self.device_mask:
                        continue
                    dev_stat = libnvml.get_device_stats(int(dev_id))
                    mem_avail_total += dev_stat.mem_total
                    mem_used_total += dev_stat.mem_used
                    mem_stats[dev_id] = Measurement(
                        Decimal(dev_stat.mem_used), Decimal(dev_stat.mem_total)
                    )
                    util_total += dev_stat.gpu_util
                    util_stats[dev_id] = Measurement(Decimal(dev_stat.gpu_util), Decimal(100))
            except ImportError:
                log.warning("gather_node_measure(): NVML library is not found")
            except LibraryError as e:
                log.warning("gather_node_measure(): {!r}", e)
        return [
            NodeMeasurement(
                MetricKey("cuda_mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey("cuda_util"),
                MetricTypes.UTILIZATION,
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
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1))
                for dev in devices
            },
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        if not self.enabled:
            return {}
        assigned_device_ids = []
        for slot_type, per_device_alloc in device_alloc.items():
            for device_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    assigned_device_ids.append(device_id)
        docker_config: Dict[str, Any] = {}
        if self.docker_version >= (19, 3, 0):
            # NOTE: You may put additional Docker container creation API params here.
            if assigned_device_ids:
                update_nested_dict(
                    docker_config,
                    {
                        "HostConfig": {
                            "DeviceRequests": [
                                {
                                    "Driver": "nvidia",
                                    "DeviceIDs": assigned_device_ids,
                                    # "all" does not work here
                                    "Capabilities": [
                                        [
                                            "utility",
                                            "compute",
                                            "video",
                                            "graphics",
                                            "display",
                                        ],
                                    ],
                                },
                            ],
                        },
                    },
                )
        else:
            update_nested_dict(
                docker_config,
                {
                    "HostConfig": {
                        "Runtime": "nvidia",
                    },
                    "Env": [
                        "NVIDIA_DRIVER_CAPABILITIES=all",
                        "NVIDIA_VISIBLE_DEVICES={}".format(",".join(assigned_device_ids)),
                    ],
                },
            )
        return docker_config

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: List[DeviceId] = []
        if SlotName("cuda.devices") in device_alloc:
            device_ids.extend(device_alloc[SlotName("cuda.devices")].keys())
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
            alloc_map.apply_allocation({
                SlotName("cuda.device"): resource_spec.allocations.get(
                    DeviceName("cuda"),
                    {},
                ).get(
                    SlotName("cuda.device"),
                    {},
                ),
            })
        else:
            alloc_map.allocations[SlotName("cuda.device")].update(
                resource_spec.allocations.get(
                    DeviceName("cuda"),
                    {},
                ).get(
                    SlotName("cuda.device"),
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
        data["CUDA_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": self.slot_types[0][0],
            "human_readable_name": "GPU",
            "description": "CUDA-capable GPU",
            "display_unit": "GPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "gpu1",
        }
