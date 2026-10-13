import logging
from collections.abc import Collection, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import Any, ClassVar

import aiodocker

from ai.backend.agent.data.device import DeviceAllocation
from ai.backend.agent.docker.resources import get_resource_spec_from_container
from ai.backend.agent.errors.resources import InvalidResourceArgument
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ai.backend.agent.stats import (
    ContainerMeasurement,
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
    SlotName,
    SlotTypes,
)
from ai.backend.logging.structured import StructuredLogger

from . import __version__
from .sysfs import (
    DEFAULT_DEV_ROOT,
    DEFAULT_SYSFS_ROOT,
    bdf_to_device_id,
    resolve_vfio_node,
    scan_vfio_gpus,
)

PREFIX = "cuda"

log = StructuredLogger(logging.getLogger(__spec__.name))


class VFIODevice(AbstractComputeDevice):
    model_name: str
    iommu_group: int
    vfio_node: str

    def __init__(
        self,
        model_name: str,
        iommu_group: int,
        vfio_node: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.iommu_group = iommu_group
        self.vfio_node = vfio_node


class CUDAVFIOPlugin(AbstractComputePlugin):
    config_watch_enabled = False
    require_explicit_allow: ClassVar[bool] = True

    key = DeviceName("cuda")
    slot_types: Sequence[tuple[SlotName, SlotTypes]] = (
        (SlotName("cuda.device"), SlotTypes("count")),
    )
    exclusive_slot_types: set[str] = set()

    memory_overrides: Mapping[str, int]
    enabled: bool = True
    sysfs_root: Path = DEFAULT_SYSFS_ROOT
    dev_root: Path = DEFAULT_DEV_ROOT

    async def init(self, context: Any | None = None) -> None:
        try:
            self.memory_overrides = self._parse_memory_overrides()
        except (ValueError, ArithmeticError) as e:
            log.warning(
                "accelerator disabled: invalid memory_overrides", plugin_name=self.key, exc_info=e
            )
            self.enabled = False
            return
        try:
            detected_devices = await self.list_devices()
        except OSError as e:
            log.warning(
                "accelerator disabled: PCI sysfs is not readable", plugin_name=self.key, exc_info=e
            )
            self.enabled = False
            return
        if not detected_devices:
            log.warning(
                "accelerator disabled: no GPU bound to vfio-pci is usable", plugin_name=self.key
            )
            self.enabled = False
            return
        log.debug("detected devices:\n{}", pformat(detected_devices))
        log.info("accelerator enabled", plugin_name=self.key, device_count=len(detected_devices))

    def _parse_memory_overrides(self) -> dict[str, int]:
        raw_overrides = self.plugin_config.get("memory_overrides") or {}
        return {str(k): int(BinarySize.finite_from_str(v)) for k, v in raw_overrides.items()}

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(
        self,
        new_plugin_config: Mapping[str, Any],
    ) -> None:
        pass

    async def list_devices(self) -> Collection[VFIODevice]:
        if not self.enabled:
            return []
        gpus = scan_vfio_gpus(self.sysfs_root, self.memory_overrides)
        return [
            VFIODevice(
                device_id=DeviceId(bdf_to_device_id(gpu.bdf)),
                device_name=self.key,
                hw_location=gpu.bdf,
                numa_node=gpu.numa_node,
                memory_size=gpu.memory_size,
                processing_units=0,
                model_name=gpu.model_name,
                iommu_group=gpu.iommu_group,
                vfio_node=gpu.vfio_node,
            )
            for gpu in gpus
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("cuda.device"): Decimal(len(devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {
            "driver": "vfio-pci",
            "iommufd": "yes" if (self.dev_root / "vfio" / "devices").is_dir() else "no",
        }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    async def gather_container_measures(
        self, ctx: StatContext, container_ids: Sequence[str]
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
        known_devices = {dev.device_id: dev for dev in await self.list_devices()}
        devices: list[dict[str, str]] = []
        for device_id in DeviceAllocation.from_device_alloc(device_alloc).attached_device_ids:
            device = known_devices.get(device_id)
            if device is None:
                raise InvalidResourceArgument(f"Unknown vfio GPU: {device_id}")
            # The node number can change when the GPU is rebound, so it is resolved at launch.
            node = resolve_vfio_node(self.sysfs_root, self.dev_root, device.hw_location)
            devices.append({
                "PathOnHost": node,
                "PathInContainer": node,
                "CgroupPermissions": "rwm",
            })
        return {"HostConfig": {"Devices": devices}}

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: list[DeviceId] = []
        if SlotName("cuda.device") in device_alloc:
            device_ids.extend(device_alloc[SlotName("cuda.device")].keys())
        available_devices = await self.list_devices()
        attached_devices: list[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": device.model_name,
                    "data": {
                        "smp": device.processing_units,
                        "mem": BinarySize(device.memory_size),
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
        alloc_map.apply_allocation({
            SlotName("cuda.device"): resource_spec.allocations.get(DeviceName("cuda"), {}).get(
                SlotName("cuda.device"), {}
            ),
        })

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[MountInfo]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": str(self.slot_types[0][0]),
            "human_readable_name": "GPU",
            "description": "CUDA-capable GPU (VFIO passthrough)",
            "display_unit": "GPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "gpu1",
        }
