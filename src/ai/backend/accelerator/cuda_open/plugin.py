import logging
import re
import uuid
from abc import ABC, abstractmethod
from collections.abc import Collection, Mapping, MutableMapping, Sequence
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Final,
    override,
)

import aiodocker
import yaml
from aiodocker.exceptions import DockerError
from aiotools import closing_async
from pydantic import BaseModel, Field

from ai.backend.agent.data.device import DeviceAllocation
from ai.backend.agent.errors.resources import InvalidResourceArgument
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ai.backend.logging import BraceStyleAdapter

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

rx_triple_version = re.compile(r"(\d+\.\d+\.\d+)")

# Engines that attach devices only through CDI, mapped to the version from which their
# Docker-compatible API honours a CDI device request. Earlier releases drop it silently.
# These engines report their own version as a component, apart from the Docker server
# version they advertise for compatibility.
CDI_ONLY_ENGINE_COMPONENTS: Final[Mapping[str, tuple[int, ...]]] = {
    "Podman Engine": (5, 4, 0),
}
MIN_DOCKER_DEVICE_REQUEST_VERSION: Final[tuple[int, ...]] = (19, 3, 0)
CDI_KIND: Final[str] = "nvidia.com/gpu"
CDI_SPEC_DIRS: Final[tuple[Path, ...]] = (Path("/etc/cdi"), Path("/var/run/cdi"))
CDI_SPEC_SUFFIXES: Final[frozenset[str]] = frozenset({".json", ".yaml", ".yml"})


class EngineComponent(BaseModel):
    """A component entry of the container engine version API response."""

    name: str = Field(validation_alias="Name")
    version: str = Field(validation_alias="Version")


class EngineVersion(BaseModel):
    """The part of the container engine version API response the plugin reads."""

    components: list[EngineComponent] = Field(
        validation_alias="Components",
        default_factory=list,
    )


def _find_cdi_only_engine(version_info: EngineVersion) -> EngineComponent | None:
    """The engine that can attach devices only through CDI, if this is one of them."""
    for component in version_info.components:
        if component.name in CDI_ONLY_ENGINE_COMPONENTS:
            return component
    return None


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


class DeviceRequest(BaseModel):
    """
    One entry of the container creation API's device request list.

    Keyed in PascalCase as the API expects, so that dumping by alias is the whole of
    the rendering.
    """

    driver: str = Field(serialization_alias="Driver")
    device_ids: Sequence[str] = Field(serialization_alias="DeviceIDs")
    # The nvidia driver rejects "all" here, so the capabilities are always spelled out.
    capabilities: Sequence[Sequence[str]] | None = Field(
        default=None,
        serialization_alias="Capabilities",
    )


class HostConfig(BaseModel):
    """The `HostConfig` fields an injector sets, mirroring where the API nests them."""

    device_requests: Sequence[DeviceRequest] | None = Field(
        default=None,
        serialization_alias="DeviceRequests",
    )
    runtime: str | None = Field(default=None, serialization_alias="Runtime")


class DeviceConfig(BaseModel):
    """
    What an injector adds to a container creation request.

    Every field defaults to null and is dropped when it stays that way, so an injector
    that attaches nothing renders to an empty payload.
    """

    host_config: HostConfig | None = Field(default=None, serialization_alias="HostConfig")
    environ: Sequence[str] | None = Field(default=None, serialization_alias="Env")


class DeviceInjector(ABC):
    """How the container engine is told to attach GPUs to a container."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def build_device_config(
        self,
        allocation: DeviceAllocation,
        devices: Collection[CUDADevice],
    ) -> DeviceConfig:
        """What to add to the container creation request to attach the allocated devices."""
        raise NotImplementedError


class LegacyRuntimeInjector(DeviceInjector):
    """Selects the nvidia runtime shim, which takes the device list from the environment."""

    @property
    @override
    def name(self) -> str:
        return "legacy-runtime"

    @override
    def build_device_config(
        self,
        allocation: DeviceAllocation,
        devices: Collection[CUDADevice],
    ) -> DeviceConfig:
        device_ids = allocation.attached_device_ids
        return DeviceConfig(
            host_config=HostConfig(runtime="nvidia"),
            environ=[
                "NVIDIA_DRIVER_CAPABILITIES=all",
                "NVIDIA_VISIBLE_DEVICES={}".format(",".join(device_ids)),
            ],
        )


class NvidiaDriverInjector(DeviceInjector):
    """Delegates to the nvidia device driver registered with the Docker daemon."""

    @property
    @override
    def name(self) -> str:
        return "nvidia-driver"

    @override
    def build_device_config(
        self,
        allocation: DeviceAllocation,
        devices: Collection[CUDADevice],
    ) -> DeviceConfig:
        device_ids = allocation.attached_device_ids
        if not device_ids:
            return DeviceConfig()
        return DeviceConfig(
            host_config=HostConfig(
                device_requests=[
                    DeviceRequest(
                        driver="nvidia",
                        device_ids=device_ids,
                        capabilities=[["utility", "compute", "video", "graphics", "display"]],
                    ),
                ],
            ),
        )


class CDIInjector(DeviceInjector):
    """
    Names the devices of a CDI kind and lets the engine apply the spec, hooks included.
    CDI identifies a GPU by its UUID while the alloc map keys it by the CUDA runtime index,
    and the two enumeration orders are not guaranteed to agree.
    """

    @property
    @override
    def name(self) -> str:
        return "cdi"

    @override
    def build_device_config(
        self,
        allocation: DeviceAllocation,
        devices: Collection[CUDADevice],
    ) -> DeviceConfig:
        device_ids = allocation.attached_device_ids
        if not device_ids:
            return DeviceConfig()
        device_uuids = {dev.device_id: dev.uuid for dev in devices}
        cdi_device_ids = []
        for device_id in device_ids:
            device_uuid = device_uuids.get(device_id)
            if device_uuid is None:
                raise InvalidResourceArgument(f"no CUDA device with the ID {device_id}")
            cdi_device_ids.append(f"{CDI_KIND}=GPU-{device_uuid}")
        return DeviceConfig(
            host_config=HostConfig(
                device_requests=[DeviceRequest(driver="cdi", device_ids=cdi_device_ids)],
            ),
        )


class CUDAPlugin(AbstractComputePlugin):
    config_watch_enabled = False

    key = DeviceName("cuda")
    slot_types: Sequence[tuple[SlotName, SlotTypes]] = (
        (SlotName("cuda.device"), SlotTypes("count")),
    )

    _device_injector: DeviceInjector = LegacyRuntimeInjector()
    device_mask: Sequence[str] = []
    enabled: bool = True

    async def init(self, context: Any | None = None) -> None:
        # Basic container engine & device access mechanism check
        try:
            async with closing_async(aiodocker.Docker()) as docker:
                docker_info = await docker.system.info()
                version_info = EngineVersion.model_validate(await docker.version())
        except DockerError:
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
            return

        device_injector = self._detect_device_injector(docker_info, version_info)
        if device_injector is None:
            log.info("CUDA acceleration is disabled.")
            self.enabled = False
            return
        self._device_injector = device_injector
        log.info("attaching GPUs via the {} mechanism.", device_injector.name)

        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [*raw_device_mask.split(",")]
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

    def _detect_device_injector(
        self,
        docker_info: Mapping[str, Any],
        version_info: EngineVersion,
    ) -> DeviceInjector | None:
        cdi_only_engine = _find_cdi_only_engine(version_info)
        if cdi_only_engine is not None:
            engine_version = self._parse_version(cdi_only_engine.version)
            if engine_version is None:
                log.error("could not detect the {} version!", cdi_only_engine.name)
                return None
            min_version = CDI_ONLY_ENGINE_COMPONENTS[cdi_only_engine.name]
            if engine_version < min_version:
                log.error(
                    "{} {} ignores CDI device requests; {} or later is required.",
                    cdi_only_engine.name,
                    self._format_version(engine_version),
                    self._format_version(min_version),
                )
                return None
            if not self._has_cdi_spec():
                log.error("could not find a CDI spec for {}!", CDI_KIND)
                return None
            return CDIInjector()

        if "nvidia" not in docker_info["Runtimes"]:
            log.error("could not detect valid NVIDIA Container Runtime!")
            return None
        docker_version = self._parse_version(docker_info["ServerVersion"])
        if docker_version is None:
            log.error("could not detect docker version!")
            return None
        if docker_version >= MIN_DOCKER_DEVICE_REQUEST_VERSION:
            return NvidiaDriverInjector()
        return LegacyRuntimeInjector()

    def _parse_version(self, raw_version: str) -> tuple[int, ...] | None:
        m = rx_triple_version.search(raw_version)
        if m is None:
            return None
        return tuple(map(int, m.group(1).split(".")))

    def _format_version(self, version: tuple[int, ...]) -> str:
        return ".".join(map(str, version))

    def _has_cdi_spec(self) -> bool:
        for spec_dir in CDI_SPEC_DIRS:
            try:
                spec_paths = sorted(spec_dir.iterdir())
            except OSError:
                continue
            for spec_path in spec_paths:
                if spec_path.suffix not in CDI_SPEC_SUFFIXES:
                    continue
                try:
                    spec = yaml.safe_load(spec_path.read_text())
                except (OSError, yaml.YAMLError):
                    continue
                if isinstance(spec, Mapping) and spec.get("kind") == CDI_KIND:
                    return True
        return False

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
            raw_info = libcudart.get_device_props(int(dev_id))
            sysfs_node_path = f"/sys/bus/pci/devices/{raw_info['pciBusID_str'].lower()}/numa_node"
            node: int | None
            try:
                node = int(Path(sysfs_node_path).read_text().strip())
            except OSError:
                node = None
            dev_uuid, raw_dev_uuid = None, raw_info.get("uuid", None)
            if raw_dev_uuid is not None:
                dev_uuid = str(uuid.UUID(bytes=raw_dev_uuid))
            else:
                dev_uuid = "00000000-0000-0000-0000-000000000000"
            if dev_uuid in self.device_mask:
                continue
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
                log.warning("gather_node_measures(): NVML library is not found")
            except LibraryError as e:
                log.warning("gather_node_measures(): {!r}", e)
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
        mem_stats: dict[str, int] = {}
        mem_sizes: dict[str, int] = {}
        util_stats: dict[str, Decimal] = {}
        number_of_devices_per_container: dict[str, int] = {}

        if self.enabled:
            mem_stats_by_device_id: dict[DeviceId, Measurement] = {}
            util_stats_by_device_id: dict[DeviceId, Measurement] = {}
            try:
                dev_count = libnvml.get_device_count()
                for dev_id in map(lambda idx: DeviceId(str(idx)), range(dev_count)):
                    if dev_id in self.device_mask:
                        continue
                    dev_stat = libnvml.get_device_stats(int(dev_id))
                    mem_stats_by_device_id[dev_id] = Measurement(
                        Decimal(dev_stat.mem_used), Decimal(dev_stat.mem_total)
                    )
                    util_stats_by_device_id[dev_id] = Measurement(
                        Decimal(dev_stat.gpu_util), Decimal(100)
                    )

                async with aiodocker.Docker() as docker:
                    for cid in container_ids:
                        try:
                            container = await docker.containers.get(cid)
                            container_info = await container.show()
                        except DockerError as e:
                            log.warning(
                                "gather_container_measures(): container {} skipped: {!r}",
                                cid,
                                e,
                            )
                            continue
                        nvidia_device_reqs = [
                            x
                            for x in container_info.get("HostConfig", {}).get("DeviceRequests")
                            or []
                            if x["Driver"] == "nvidia"
                        ]
                        if not nvidia_device_reqs:
                            continue

                        mem_stats[cid] = 0
                        mem_sizes[cid] = 0
                        util_stats[cid] = Decimal("0")
                        number_of_devices_per_container[cid] = 0

                        for device_id in nvidia_device_reqs[0]["DeviceIDs"]:
                            mem_stat = mem_stats_by_device_id[DeviceId(device_id)]
                            util_stat = util_stats_by_device_id[DeviceId(device_id)]
                            mem_stats[cid] += int(mem_stat.value)
                            mem_sizes[cid] += int(mem_stat.capacity or 0)
                            util_stats[cid] += Decimal(util_stat.value)
                            number_of_devices_per_container[cid] += 1
            except ImportError:
                log.warning("gather_container_measures(): NVML library is not found")
            except LibraryError as e:
                log.warning("gather_container_measures(): {!r}", e)

        return [
            ContainerMeasurement(
                MetricKey("cuda_mem"),
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
                MetricKey("cuda_util"),
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
        device_config = self._device_injector.build_device_config(
            DeviceAllocation.from_device_alloc(device_alloc),
            await self.list_devices(),
        )
        return device_config.model_dump(by_alias=True, exclude_none=True)

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

        active_device_id_set: set[DeviceId] = set()
        for slot_type, per_device_alloc in device_alloc.items():
            for dev_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    active_device_id_set.add(dev_id)
        active_device_ids = sorted(active_device_id_set, key=lambda v: int(v))
        data["CUDA_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        data["CUDA_RESOURCE_VIRTUALIZED"] = "0"
        return data

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
            "description": "CUDA-capable GPU",
            "display_unit": "GPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "gpu1",
        }
