import asyncio
import json
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
import aiohttp
import attr

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
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
    StatContext,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.common.types import (
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


@attr.s(auto_attribs=True)
class CUDADevice(AbstractComputeDevice):
    model_name: str
    uuid: str


class CUDAPlugin(AbstractComputePlugin):

    config_watch_enabled = False

    key = DeviceName("cuda")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("cuda.device"), SlotTypes("count")),
    )

    nvdocker_version: Tuple[int, ...] = (0, 0, 0)
    docker_version: Tuple[int, ...] = (0, 0, 0)

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True

    async def init(self, context: Any = None) -> None:
        rx_triple_version = re.compile(r"(\d+\.\d+\.\d+)")
        # Check nvidia-docker and docker versions
        try:
            proc = await asyncio.create_subprocess_exec(
                "nvidia-docker",
                "version",
                "-f",
                "{{json .}}",
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            lines = stdout.decode().splitlines()
        except FileNotFoundError:
            log.warning("nvidia-docker is not installed.")
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
            return
        m = rx_triple_version.search(lines[0])
        if m:
            self.nvdocker_version = tuple(map(int, m.group(1).split(".")))
        else:
            log.error("could not detect nvidia-docker version!")
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
            return
        docker_version_data = json.loads(lines[1])
        m = rx_triple_version.search(docker_version_data["Server"]["Version"])
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
            log.info("nvidia-docker version: {}", self.nvdocker_version)
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
            sysfs_node_path = (
                "/sys/bus/pci/devices/" f"{raw_info['pciBusID_str'].lower()}/numa_node"
            )
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
                device_id=dev_id,
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
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey("cuda_util"),
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
        return []

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: (
                    DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1))
                )
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
        if self.nvdocker_version[0] == 1:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(raise_for_status=True, timeout=timeout) as sess:
                try:
                    nvdocker_url = "http://localhost:3476/docker/cli/json"
                    async with sess.get(nvdocker_url) as resp:
                        nvidia_params = await resp.json()
                except aiohttp.ClientError:
                    raise RuntimeError("NVIDIA Docker plugin is not available.")

            volumes = await docker.volumes.list()
            existing_volumes = set(vol["Name"] for vol in volumes["Volumes"])
            required_volumes = set(vol.split(":")[0] for vol in nvidia_params["Volumes"])
            missing_volumes = required_volumes - existing_volumes
            binds = []
            for vol_name in missing_volumes:
                for vol_param in nvidia_params["Volumes"]:
                    if vol_param.startswith(vol_name + ":"):
                        _, _, permission = vol_param.split(":")
                        driver = nvidia_params["VolumeDriver"]
                        await docker.volumes.create(
                            {
                                "Name": vol_name,
                                "Driver": driver,
                            }
                        )
            for vol_name in required_volumes:
                for vol_param in nvidia_params["Volumes"]:
                    if vol_param.startswith(vol_name + ":"):
                        _, mount_pt, permission = vol_param.split(":")
                        binds.append("{}:{}:{}".format(vol_name, mount_pt, permission))
            devices = []
            for dev in nvidia_params["Devices"]:
                m = re.search(r"^/dev/nvidia(\d+)$", dev)
                if m is None:
                    # Always add non-GPU device files required by the driver.
                    # (e.g., nvidiactl, nvidia-uvm, ... etc.)
                    devices.append(dev)
                    continue
                device_id = DeviceId(m.group(1))
                if device_id not in assigned_device_ids:
                    continue
                devices.append(dev)
            devices = [
                {
                    "PathOnHost": dev,
                    "PathInContainer": dev,
                    "CgroupPermissions": "mrw",
                }
                for dev in devices
            ]
            return {
                "HostConfig": {
                    "Binds": binds,
                    "Devices": devices,
                },
            }
        elif self.nvdocker_version[0] == 2:
            device_list_str = ",".join(sorted(assigned_device_ids))
            if self.docker_version >= (19, 3, 0):
                docker_config: Dict[str, Any] = {}
                if assigned_device_ids:
                    docker_config.update(
                        {
                            "HostConfig": {
                                "DeviceRequests": [
                                    {
                                        "Driver": "nvidia",
                                        "DeviceIDs": assigned_device_ids,
                                        # "all" does not work here
                                        "Capabilities": [
                                            ["utility", "compute", "video", "graphics", "display"],
                                        ],
                                    },
                                ],
                            },
                        }
                    )
                return docker_config
            else:
                return {
                    "HostConfig": {
                        "Runtime": "nvidia",
                    },
                    "Env": [
                        f"NVIDIA_VISIBLE_DEVICES={device_list_str}",
                    ],
                }
        else:
            raise RuntimeError("BUG: should not be reached here!")

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
                attached_devices.append(
                    {  # TODO: update common.types.DeviceModelInfo
                        "device_id": device.device_id,
                        "model_name": device.model_name,
                        "data": {
                            "smp": proc,
                            "mem": mem,
                        },
                    }
                )
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
            alloc_map.apply_allocation(
                {
                    SlotName("cuda.device"): resource_spec.allocations.get(
                        DeviceName("cuda"),
                        {},
                    ).get(
                        SlotName("cuda.device"),
                        {},
                    ),
                }
            )
        else:
            alloc_map.allocations[SlotName("cuda.device")].update(
                resource_spec.allocations.get(DeviceName("cuda"), {},).get(
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
