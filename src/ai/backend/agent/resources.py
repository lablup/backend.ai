from __future__ import annotations

import asyncio
import copy
import logging
import pprint
import textwrap
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from collections.abc import (
    Collection,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Protocol,
    Self,
    TextIO,
    cast,
)

import aiodocker
import attrs
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

import ai.backend.agent.alloc_map as alloc_map_mod
from ai.backend.agent.config.unified import AgentUnifiedConfig, ResourceAllocationMode
from ai.backend.agent.errors.resources import (
    AgentIdNotFoundError,
    InvalidResourceConfigError,
    ResourceOverAllocatedError,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.common.types import (
    AcceleratorMetadata,
    AgentId,
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    HardwareMetadata,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceSlot,
    SlotName,
    SlotTypes,
    aobject,
)
from ai.backend.logging import BraceStyleAdapter

# Expose legacy import names for plugins
from .affinity_map import AffinityHint, AffinityMap, AffinityPolicy
from .alloc_map import AbstractAllocMap as AbstractAllocMap
from .alloc_map import AllocationStrategy as AllocationStrategy
from .alloc_map import DeviceSlotInfo as DeviceSlotInfo
from .alloc_map import DiscretePropertyAllocMap as DiscretePropertyAllocMap
from .alloc_map import FractionAllocMap as FractionAllocMap
from .exception import ResourceError
from .stats import ContainerMeasurement, NodeMeasurement, ProcessMeasurement, StatContext
from .types import AbstractAgentDiscovery, MountInfo, get_agent_discovery
from .types import Container as SessionContainer

if TYPE_CHECKING:
    from io import TextIOWrapper

    from aiofiles.threadpool.text import AsyncTextIOWrapper


type DeviceAllocation = Mapping[SlotName, Mapping[DeviceId, Decimal]]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
known_slot_types: Mapping[SlotName, SlotTypes] = {}


def _combine_mappings(mappings: list[Mapping[SlotName, Decimal]]) -> dict[SlotName, Decimal]:
    combined: dict[SlotName, Decimal] = {}
    for mapping in mappings:
        if set(combined.keys()) & set(mapping.keys()):
            raise ValueError(
                f"Duplicate keys found in devices: {combined.keys()} and {mapping.keys()}"
            )
        combined = {**combined, **mapping}
    return combined


# Type alias for unified device assignments structure
# Both AUTO_SPLIT (generated) and MANUAL (from config) produce this
type DeviceAssignments = Mapping[AgentId, Mapping[DeviceName, Sequence[DeviceId]]]


def _natural_sort_key(device_id: DeviceId) -> list[str | int]:
    """
    Generate a sort key for natural sorting of device IDs.

    Splits the string into alternating text/number chunks, converting numbers
    to integers for proper numeric comparison. This is the standard natural sort
    algorithm used by file explorers (Finder, Explorer, etc.).

    Handles numbers anywhere in the string, not just suffixes.

    Examples:
        "0" -> ["", 0, ""]
        "10" -> ["", 10, ""]
        "cuda0" -> ["cuda", 0, ""]
        "cuda10" -> ["cuda", 10, ""]
        "nvme0n1p1" -> ["nvme", 0, "n", 1, "p", 1, ""]
        "device" -> ["device"]
    """
    import re

    parts = re.split(r"(\d+)", str(device_id))
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def distribute_devices(
    device_ids: Sequence[DeviceId],
    agent_ids: Sequence[AgentId],
) -> dict[AgentId, list[DeviceId]]:
    """
    Distribute devices across agents using divmod fill-from-front.

    For N devices across M agents:
    - q, r = divmod(N, M)
    - First r agents get (q + 1) devices
    - Remaining agents get q devices
    - Devices are assigned in natural sorted order, filling agents from front

    Natural sort handles both numeric IDs (0, 1, 10) and prefixed IDs (cuda0, cuda10).

    Args:
        device_ids: Device IDs to distribute
        agent_ids: Agent IDs to distribute to

    Returns:
        Mapping of agent_id -> assigned device IDs
    """
    if not agent_ids:
        return {}

    sorted_ids = sorted(device_ids, key=_natural_sort_key)
    num_devices = len(sorted_ids)
    q, r = divmod(num_devices, len(agent_ids))

    result: dict[AgentId, list[DeviceId]] = {}
    device_idx = 0

    for i, agent_id in enumerate(agent_ids):
        count = q + 1 if i < r else q
        end_idx = min(device_idx + count, num_devices)
        result[agent_id] = sorted_ids[device_idx:end_idx]
        device_idx = end_idx

    return result


class DevicePartitioner(Protocol):
    """
    Protocol for generating device assignments in AUTO_SPLIT mode.

    NOTE: This is ONLY used for AUTO_SPLIT. For MANUAL mode, assignments
    are read directly from config. Both modes then use the same
    _apply_device_assignments() function.
    """

    device_name: DeviceName

    def generate_assignments(
        self,
        devices: Sequence[AbstractComputeDevice],
        agent_ids: Sequence[AgentId],
    ) -> Mapping[AgentId, Sequence[DeviceId]]:
        """
        Generate device assignments for AUTO_SPLIT mode.
        Returns mapping of agent_id -> list of assigned device IDs.
        """
        ...


class WholeDevicePartitioner:
    """
    Base partitioner for whole-device assignment.
    Uses fill-from-front with divmod distribution.
    """

    def __init__(self, device_name: DeviceName) -> None:
        self.device_name = device_name

    def generate_assignments(
        self,
        devices: Sequence[AbstractComputeDevice],
        agent_ids: Sequence[AgentId],
    ) -> Mapping[AgentId, Sequence[DeviceId]]:
        device_ids = [d.device_id for d in devices]
        return distribute_devices(device_ids, agent_ids)


class SharedDevicePartitioner:
    """
    Partitioner for devices shared by all agents.

    All agents get the same device IDs.
    Slot amount splitting is handled separately in _apply_device_assignments().
    """

    def __init__(self, device_name: DeviceName) -> None:
        self.device_name = device_name

    def generate_assignments(
        self,
        devices: Sequence[AbstractComputeDevice],
        agent_ids: Sequence[AgentId],
    ) -> Mapping[AgentId, Sequence[DeviceId]]:
        if not devices:
            raise ResourceError(
                f"No devices found for {self.device_name} plugin. "
                "This is a fatal configuration error."
            )
        if len(devices) > 1:
            log.warning(
                "Plugin {} has multiple devices ({}), using only the first one",
                self.device_name,
                [d.device_id for d in devices],
            )
        device_id = devices[0].device_id
        return {agent_id: [device_id] for agent_id in agent_ids}


@dataclass
class GlobalDeviceInfo:
    """Global device info without alloc_map - used for system-wide view."""

    plugin: AbstractComputePlugin
    devices: Collection[AbstractComputeDevice]


@attrs.define(auto_attribs=True, slots=True)
class ComputerContext:
    instance: AbstractComputePlugin
    devices: Collection[AbstractComputeDevice]
    alloc_map: AbstractAllocMap


@dataclass
class DeviceView:
    device: DeviceName
    slot: SlotName
    device_alloc: Mapping[DeviceId, Decimal]


@attrs.define(slots=True)
class KernelResourceSpec:
    """
    This struct-like object stores the kernel resource allocation information
    with serialization and deserialization.

    It allows seamless reconstruction of allocations even when the agent restarts
    while kernel containers are running.
    """

    slots: ResourceSlot
    """Stores the original user-requested resource slots."""

    allocations: MutableMapping[DeviceName, Mapping[SlotName, Mapping[DeviceId, Decimal]]]
    """
    Represents the resource allocations for each slot (device) type and devices.
    """

    scratch_disk_size: int
    """The size of scratch disk. (not implemented yet)"""

    mounts: list[Mount] = attrs.Factory(list)
    """The mounted vfolder list."""

    unified_devices: Iterable[tuple[DeviceName, SlotName]] = attrs.Factory(list)
    """
    Represents unified devices mounted to the kernel.
    """

    def freeze(self) -> None:
        """Replace the attribute setter to make it immutable."""
        # TODO: implement
        pass

        # def _frozen_setattr(self, name, value):
        #     raise RuntimeError("tried to modify a frozen KernelResourceSpec object")

        # self.mounts = tuple(self.mounts)  # type: ignore
        # # TODO: wrap slots and allocations with frozendict?
        # setattr(self, '__setattr__', _frozen_setattr)  # <-- __setattr__ is read-only... :(

    @property
    def device_list(self) -> Iterable[DeviceView]:
        """
        View of effective list of devices mounted to kernel, aggregating both non-unified and unified devices.
        DeviceView representing unified devices will always have empty `device_alloc` map.
        Unlike the `allocations` property, this view will not list slots with zero allocation - that is, slots without any alloc map defined.
        """
        devices = []
        for device, allocs in self.allocations.items():
            for slot, device_alloc in allocs.items():
                alloc_sum = Decimal(0)
                for dev_id, per_dev_alloc in device_alloc.items():
                    alloc_sum += per_dev_alloc
                if alloc_sum > 0:
                    devices.append(DeviceView(device, slot, device_alloc))
        for device, slot in self.unified_devices:
            devices.append(DeviceView(device, slot, {}))

        return devices

    def write_to_string(self) -> str:
        mounts_str = ",".join(map(str, self.mounts))
        slots_str = dump_json_str({k: str(v) for k, v in self.slots.items()})
        unified_devices_str = dump_json_str(self.unified_devices)

        resource_str = ""
        resource_str += f"SCRATCH_SIZE={BinarySize(self.scratch_disk_size):m}\n"
        resource_str += f"MOUNTS={mounts_str}\n"
        resource_str += f"SLOTS={slots_str}\n"
        resource_str += f"UNIFIED_DEVICES={unified_devices_str}\n"

        for device_name, slots in self.allocations.items():
            for slot_name, per_device_alloc in slots.items():
                if not (slot_name.startswith(f"{device_name}.") or slot_name == device_name):
                    raise ValueError(
                        f"device_name ({device_name}) must be a prefix of slot_name ({slot_name})"
                    )
                pieces = []
                for dev_id, alloc in per_device_alloc.items():
                    if known_slot_types.get(slot_name, "count") == "bytes":
                        pieces.append(f"{dev_id}:{BinarySize(alloc):s}")
                    else:
                        pieces.append(f"{dev_id}:{alloc}")
                alloc_str = ",".join(pieces)
                resource_str += f"{slot_name.upper()}_SHARES={alloc_str}\n"

        return resource_str

    def write_to_file(self, file: TextIO) -> None:
        file.write(self.write_to_string())

    @classmethod
    def read_from_string(cls, text: str) -> Self:
        kvpairs = {}
        for line in text.split("\n"):
            if "=" not in line:
                continue
            key, val = line.strip().split("=", maxsplit=1)
            kvpairs[key] = val
        allocations = cast(
            MutableMapping[
                DeviceName,
                MutableMapping[SlotName, Mapping[DeviceId, Decimal]],
            ],
            defaultdict(lambda: defaultdict(Decimal)),
        )
        for key, val in kvpairs.items():
            if key.endswith("_SHARES"):
                slot_name = SlotName(key[:-7].lower())
                device_name = DeviceName(slot_name.split(".")[0])
                per_device_alloc: MutableMapping[DeviceId, Decimal] = {}
                for entry in val.split(","):
                    raw_dev_id, _, raw_alloc = entry.partition(":")
                    if not raw_dev_id or not raw_alloc:
                        continue
                    dev_id = DeviceId(raw_dev_id)
                    try:
                        if known_slot_types.get(slot_name, "count") == "bytes":
                            alloc = Decimal(BinarySize.from_str(raw_alloc))
                        else:
                            alloc = Decimal(raw_alloc)
                    except KeyError as e:
                        log.warning(
                            "A previously launched container has "
                            "unknown slot type: {}. Ignoring it.",
                            e.args[0],
                        )
                        continue
                    per_device_alloc[dev_id] = alloc
                allocations[device_name][slot_name] = per_device_alloc
        mounts = [Mount.from_str(m) for m in kvpairs["MOUNTS"].split(",") if m]
        return cls(
            scratch_disk_size=BinarySize.finite_from_str(kvpairs["SCRATCH_SIZE"]),
            allocations=dict(allocations),
            unified_devices=load_json(kvpairs.get("UNIFIED_DEVICES") or "[]"),
            slots=ResourceSlot.from_json(load_json(kvpairs["SLOTS"])),
            mounts=mounts,
        )

    @classmethod
    def read_from_file(cls, file: TextIOWrapper) -> Self:
        text = "\n".join(file.readlines())
        return cls.read_from_string(text)

    @classmethod
    async def aread_from_file(cls, file: AsyncTextIOWrapper) -> Self:
        text = "\n".join(await file.readlines())  # type: ignore
        return cls.read_from_string(text)

    def to_json_serializable_dict(self) -> Mapping[str, Any]:
        o = attrs.asdict(self)
        for slot_name, alloc in o["slots"].items():
            if known_slot_types.get(slot_name, "count") == "bytes":
                o["slots"] = f"{BinarySize(alloc):s}"
            else:
                o["slots"] = str(alloc)
        serialized_allocations = {}
        for dev_name, dev_alloc in o["allocations"].items():
            serialized_dev_alloc = {}
            for slot_name, per_device_alloc in dev_alloc.items():
                serialized_per_device_alloc = {}
                for dev_id, alloc in per_device_alloc.items():
                    if known_slot_types.get(slot_name, "count") == "bytes":
                        serialized_alloc = f"{BinarySize(alloc):s}"
                    else:
                        serialized_alloc = str(alloc)
                    serialized_per_device_alloc[str(dev_id)] = serialized_alloc
                serialized_dev_alloc[str(slot_name)] = serialized_per_device_alloc
            serialized_allocations[str(dev_name)] = serialized_dev_alloc
        o["allocations"] = serialized_allocations
        o["mounts"] = list(map(str, self.mounts))
        return o

    def to_json(self) -> str:
        return dump_json_str(self.to_json_serializable_dict())

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def validate(value: Any) -> KernelResourceSpec:
            return cls(
                slots=value.slots,
                allocations=value.allocations,
                scratch_disk_size=value.scratch_disk_size,
                mounts=value.mounts,
            )

        return core_schema.no_info_plain_validator_function(validate)


class AbstractComputeDevice:
    device_id: DeviceId
    hw_location: str  # either PCI bus ID or arbitrary string
    memory_size: int  # bytes of available per-accelerator memory
    processing_units: int  # number of processing units (e.g., cores, SMP)
    _device_name: Optional[DeviceName]
    numa_node: Optional[int]  # NUMA node ID (None if not applicable)

    def __init__(
        self,
        device_id: DeviceId,
        hw_location: str,
        memory_size: int,
        processing_units: int,
        numa_node: Optional[int] = None,
        device_name: Optional[DeviceName] = None,
    ) -> None:
        self.device_id = device_id
        self.hw_location = hw_location
        self.memory_size = memory_size
        self.processing_units = processing_units
        self._device_name = device_name
        self.numa_node = numa_node

    @property
    def device_name(self) -> DeviceName:
        if self._device_name:
            return self._device_name
        return DeviceName(self.__class__.__name__.removesuffix("Device").lower())

    def __hash__(self) -> int:
        return hash(f"{self.device_name}-{self.device_id}")

    def __eq__(self, __o: object) -> bool:
        return hash(self) == hash(__o)


class AbstractComputePlugin(AbstractPlugin, metaclass=ABCMeta):
    key: DeviceName = DeviceName("accelerator")
    slot_types: Sequence[tuple[SlotName, SlotTypes]]
    exclusive_slot_types: set[str]

    @abstractmethod
    def get_metadata(self) -> AcceleratorMetadata:
        """
        Return human-readable information of the accelerator managed
        by the plugin.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_devices(self) -> Collection[AbstractComputeDevice]:
        """
        Return the list of accelerator devices, as read as physically
        on the host.
        """
        raise NotImplementedError

    @abstractmethod
    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        """
        Return available slot amounts for each slot key.
        """
        raise NotImplementedError

    @abstractmethod
    def get_version(self) -> str:
        """
        Return the version string of the plugin.
        """
        raise NotImplementedError

    @abstractmethod
    async def extra_info(self) -> Mapping[str, str]:
        """
        Return extra information related to this plugin,
        such as the underlying driver version and feature flags.
        """
        return {}

    @abstractmethod
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        """
        Return the system-level and device-level statistic metrics.

        It may return any number of metrics using different statistics key names in the
        returning map.
        Note that the key must not conflict with other accelerator plugins and must not
        contain dots.
        """
        raise NotImplementedError

    @abstractmethod
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        """
        Return the container-level statistic metrics.
        """
        raise NotImplementedError

    @abstractmethod
    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        """
        Return the process statistic metrics in container.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_alloc_map(self) -> AbstractAllocMap:
        """
        Create and return an allocation map for this plugin.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        """
        Return the library hook paths used by the plugin (optional).

        :param str distro: The target Linux distribution such as "ubuntu16.04" or
                           "alpine3.8"
        :param str arch: The target CPU architecture such as "amd64"
        """
        return []

    @abstractmethod
    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, Any]:
        """
        When starting a new container, generate device-specific options for the
        docker container create API as a dictionary, referring the given allocation
        map.  The agent will merge it with its own options.
        """
        return {}

    async def generate_resource_data(self, device_alloc: DeviceAllocation) -> Mapping[str, str]:
        """
        Generate extra resource.txt key-value pair sets to be used by the plugin's
        own hook libraries in containers.
        """
        return {}

    @abstractmethod
    async def restore_from_container(
        self,
        container: SessionContainer,
        alloc_map: AbstractAllocMap,
    ) -> None:
        """
        When the agent restarts, retore the allocation map from the container
        metadata dictionary fetched from aiodocker.
        """
        pass

    @abstractmethod
    async def get_attached_devices(
        self,
        device_alloc: DeviceAllocation,
    ) -> Sequence[DeviceModelInfo]:
        """
        Make up container-attached device information with allocated device id.
        """
        return []

    async def get_node_hwinfo(self) -> HardwareMetadata:
        raise NotImplementedError

    @abstractmethod
    async def get_docker_networks(
        self,
        device_alloc: DeviceAllocation,
    ) -> list[str]:
        """
        Returns reference string (e.g. Id, name, ...) of docker networks
        to attach to container for accelerator to work properly.
        """
        return []

    @abstractmethod
    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: DeviceAllocation,
    ) -> list[MountInfo]:
        """
        Populates additional files/directories under `source_path`
        to mount to container and returns `MountInfo`.
        Agent will then read this `MountInfo`s and mount files/directories.
        """
        return []

    def get_additional_gids(self) -> list[int]:
        """
        Override this function to pass the additional GIDs the 'work' user will belong to in the container.
        This is useful when the accelerator plugin assumes that the 'work' is part of a specific group.
        """
        return []

    def get_additional_allowed_syscalls(self) -> list[str]:
        """
        Returns system calls allowed within the container.
        These system calls will be additionally allowed in addition to those allowed by the default seccomp profile.

        e.g., ["io_uring_enter", "io_uring_setup", "io_uring_register"] for enabling io_uring in the container.
        """
        return []


type ComputersMap = Mapping[DeviceName, ComputerContext]
type GlobalDeviceMap = Mapping[DeviceName, GlobalDeviceInfo]
type SlotsMap = Mapping[SlotName, Decimal]


class ResourceAllocator(aobject):
    local_config: AgentUnifiedConfig
    etcd: AsyncEtcd
    agent_configs: Sequence[AgentUnifiedConfig]

    global_devices: GlobalDeviceMap
    available_total_slots: SlotsMap

    agent_computers: Mapping[AgentId, ComputersMap]
    agent_reserved_slots: Mapping[AgentId, SlotsMap]
    agent_resource_scaling_factor: Mapping[AgentId, SlotsMap]

    @property
    def num_agents(self) -> int:
        return len(self.agent_configs)

    def __init__(self, local_config: AgentUnifiedConfig, etcd: AsyncEtcd) -> None:
        self.local_config = local_config
        self.etcd = etcd
        self.agent_configs = local_config.get_agent_configs()

    async def __ainit__(self) -> None:
        alloc_map_mod.log_alloc_map = self.local_config.debug.log_alloc_map
        self.global_devices = await self._create_global_devices()

        total_slots = await self._calculate_total_slots()
        self.available_total_slots = self._calculate_available_total_slots(total_slots)

        # Build agent computers with device assignments (new flow)
        self.agent_computers = await self._build_agent_computers()

        # Calculate reserved slots and resource scaling factor from allocated slots
        agent_reserved_slots: dict[AgentId, SlotsMap] = {}
        agent_resource_scaling_factor: dict[AgentId, SlotsMap] = {}
        for agent_config in self.agent_configs:
            agent_id = AgentId(agent_config.agent.defaulted_id)
            allocated_slots = self._get_agent_allocated_slots(agent_id)
            reserved_slots = self._calculate_reserved_slots(allocated_slots, total_slots)
            resource_scaling_factor = self._calculate_resource_scaling_factor(allocated_slots)

            agent_reserved_slots[agent_id] = reserved_slots
            agent_resource_scaling_factor[agent_id] = resource_scaling_factor

        self.agent_reserved_slots = agent_reserved_slots
        self.agent_resource_scaling_factor = agent_resource_scaling_factor
        self._ensure_slots_are_not_overallocated()

    async def __aexit__(self, *exc_info) -> None:
        for _, device_info in self.global_devices.items():
            try:
                await device_info.plugin.cleanup()
            except Exception:
                log.exception("Failed to clean up computer instance:")

    def get_computers(self, agent_id: AgentId) -> ComputersMap:
        if agent_id not in self.agent_computers:
            raise AgentIdNotFoundError(f"Agent ID {agent_id} not in computers")
        return self.agent_computers[agent_id]

    async def get_updated_slots(self, agent_id: AgentId) -> SlotsMap:
        """
        Finalize the resource slots from the resource slots scanned by each device plugin,
        excluding reserved capacities for the system and agent itself.
        """

        scanned_slots = await self._scan_available_resources()
        if agent_id not in self.agent_reserved_slots:
            raise AgentIdNotFoundError(f"Agent ID {agent_id} not in reserved slots")
        reserved_slots = self.agent_reserved_slots[agent_id]
        usable_slots: dict[SlotName, Decimal] = {}

        for slot_name, slot_capacity in scanned_slots.items():
            if slot_name == SlotName("mem"):
                mem_reserved = int(reserved_slots.get(slot_name, 0))
                mem_align = int(self.local_config.resource.memory_align_size)
                mem_usable, mem_reserved = align_memory(
                    int(slot_capacity), mem_reserved, align=mem_align
                )
                usable_capacity = Decimal(mem_usable)
                log.debug(
                    "usable-mem: {:m}, reserved-mem: {:m} after {:m} alignment",
                    BinarySize(mem_usable),
                    BinarySize(mem_reserved),
                    BinarySize(mem_align),
                )
            else:
                usable_capacity = max(
                    Decimal(0), slot_capacity - reserved_slots.get(slot_name, Decimal(0))
                )
            usable_slots[slot_name] = usable_capacity

        return usable_slots

    def get_resource_scaling_factor(self, agent_id: AgentId) -> SlotsMap:
        if agent_id not in self.agent_resource_scaling_factor:
            raise AgentIdNotFoundError(f"Agent ID {agent_id} not in computers")
        return self.agent_resource_scaling_factor[agent_id]

    @cached_property
    def _cpu_device_name(self) -> DeviceName:
        """Find CPU device name by checking for SlotTypes.COUNT in plugin's slot_types."""
        for device_info in self.global_devices.values():
            slot_types_dict = dict(device_info.plugin.slot_types)
            if SlotTypes.COUNT in slot_types_dict.values():
                return device_info.plugin.key
        raise InvalidResourceConfigError("CPU plugin not found")

    @cached_property
    def _mem_device_name(self) -> DeviceName:
        """Find memory device name by checking for SlotName('mem') with SlotTypes.BYTES."""
        for device_info in self.global_devices.values():
            slot_types_dict = dict(device_info.plugin.slot_types)
            if (
                SlotName("mem") in slot_types_dict
                and slot_types_dict[SlotName("mem")] == SlotTypes.BYTES
            ):
                return device_info.plugin.key
        raise InvalidResourceConfigError("Memory plugin not found")

    def _is_memory_plugin(self, plugin: AbstractComputePlugin) -> bool:
        """Check if a plugin is the memory plugin by examining its slot types."""
        slot_types_dict = dict(plugin.slot_types)
        return (
            SlotName("mem") in slot_types_dict
            and slot_types_dict[SlotName("mem")] == SlotTypes.BYTES
        )

    async def _create_global_devices(self) -> GlobalDeviceMap:
        """Load plugins and list devices - no alloc_map creation."""
        computer_plugins = await self._load_resources()

        devices: dict[DeviceName, GlobalDeviceInfo] = {}
        for name, plugin in computer_plugins.items():
            device_list = await plugin.list_devices()
            devices[name] = GlobalDeviceInfo(plugin, device_list)
        return devices

    async def _calculate_total_slots(self) -> SlotsMap:
        total_slots: dict[SlotName, Decimal] = defaultdict(lambda: Decimal("0"))
        for device_info in self.global_devices.values():
            slots = await device_info.plugin.available_slots()
            for slot_name, amount in slots.items():
                total_slots[slot_name] += amount
        return total_slots

    def _calculate_available_total_slots(self, total_slots: SlotsMap) -> SlotsMap:
        reserved_resources = {
            SlotName("cpu"): Decimal(self.local_config.resource.reserved_cpu),
            SlotName("mem"): Decimal(self.local_config.resource.reserved_mem),
            SlotName("disk"): Decimal(self.local_config.resource.reserved_disk),
        }

        available_slots: dict[SlotName, Decimal] = {}
        for slot_name, total_slot in total_slots.items():
            reserved_slot = reserved_resources.get(slot_name, Decimal("0"))
            if total_slot < reserved_slot:
                raise InvalidResourceConfigError(
                    f"Slot {slot_name} reserved for {reserved_slot}, "
                    f"which is larger than total slot available {total_slot}"
                )
            available_slots[slot_name] = total_slot - reserved_slot
        return available_slots

    def _calculate_reserved_slots(self, device_slots: SlotsMap, total_slots: SlotsMap) -> SlotsMap:
        reserved_slots: dict[SlotName, Decimal] = {}
        for slot_name, slot in device_slots.items():
            total_slot = total_slots[slot_name]
            reserved_slots[slot_name] = max(total_slot - slot, Decimal(0))
        return reserved_slots

    def _calculate_resource_scaling_factor(self, allocated_slots: SlotsMap) -> SlotsMap:
        match self.local_config.resource.allocation_mode:
            case ResourceAllocationMode.SHARED:
                return defaultdict(lambda: Decimal(1.0))
            case ResourceAllocationMode.AUTO_SPLIT:
                return defaultdict(lambda: Decimal(1.0) / Decimal(self.num_agents))
            case ResourceAllocationMode.MANUAL:
                if (
                    SlotName("cpu") not in allocated_slots
                    or SlotName("cpu") not in self.available_total_slots
                ):
                    raise ValueError("CPU not in allocated or total slots seen")
                if (
                    SlotName("mem") not in allocated_slots
                    or SlotName("mem") not in self.available_total_slots
                ):
                    raise ValueError("Memory not in allocated or total slots seen")
                return {
                    slot_name: slot / self.available_total_slots[slot_name]
                    for slot_name, slot in allocated_slots.items()
                }

    def _ensure_slots_are_not_overallocated(self) -> None:
        if self.local_config.resource.allocation_mode != ResourceAllocationMode.MANUAL:
            return

        allocated_slots: dict[SlotName, Decimal] = defaultdict(lambda: Decimal("0"))
        for agent_reserved_slots in self.agent_reserved_slots.values():
            for slot_name in self.available_total_slots.keys():
                available_total_slot = self.available_total_slots[slot_name]
                allocated_slot = available_total_slot - agent_reserved_slots[slot_name]
                allocated_slots[slot_name] += allocated_slot

        for slot_name, allocated_slot in allocated_slots.items():
            available_total_slot = self.available_total_slots[slot_name]
            if available_total_slot < allocated_slot:
                raise ResourceOverAllocatedError(
                    f"Resource slot {slot_name} was manually allocated {allocated_slot} across "
                    f"all agents when total capacity is {available_total_slot}."
                )

    async def _build_agent_computers(self) -> Mapping[AgentId, ComputersMap]:
        """Build agent computer contexts with device partitioning."""

        # Create base computer contexts for all agents
        agent_computers = await self._create_base_agent_computers()

        match self.local_config.resource.allocation_mode:
            case ResourceAllocationMode.SHARED:
                # No partitioning needed - all agents share all devices
                return agent_computers

            case ResourceAllocationMode.AUTO_SPLIT:
                # Generate assignments via partitioners
                assignments = self._generate_auto_split_assignments()
                return self._apply_device_assignments(agent_computers, assignments)

            case ResourceAllocationMode.MANUAL:
                # Read assignments from config
                assignments = self._read_manual_assignments()
                self._validate_assignments(assignments)
                return self._apply_device_assignments(agent_computers, assignments)

    async def _create_base_agent_computers(self) -> dict[AgentId, ComputersMap]:
        """Create base ComputerContext for each agent with all devices."""
        agent_computers: dict[AgentId, ComputersMap] = {}

        for agent_config in self.agent_configs:
            agent_id = AgentId(agent_config.agent.defaulted_id)
            computers: dict[DeviceName, ComputerContext] = {}
            for device_name, device_info in self.global_devices.items():
                computers[device_name] = ComputerContext(
                    instance=device_info.plugin,
                    devices=list(device_info.devices),
                    alloc_map=await device_info.plugin.create_alloc_map(),
                )
            agent_computers[agent_id] = computers

        return agent_computers

    def _generate_auto_split_assignments(self) -> DeviceAssignments:
        """
        Generate device assignments for AUTO_SPLIT mode.
        Uses partitioners to compute fill-from-front distribution.
        """
        agent_ids = [AgentId(cfg.agent.defaulted_id) for cfg in self.agent_configs]
        assignments: dict[AgentId, dict[DeviceName, list[DeviceId]]] = {
            agent_id: {} for agent_id in agent_ids
        }

        for device_name, device_info in self.global_devices.items():
            partitioner = self._get_partitioner(device_info)
            device_assignments = partitioner.generate_assignments(
                list(device_info.devices), agent_ids
            )

            for agent_id, device_ids in device_assignments.items():
                assignments[agent_id][device_name] = list(device_ids)

        return assignments

    def _get_partitioner(self, device_info: GlobalDeviceInfo) -> DevicePartitioner:
        """Get the appropriate partitioner for a device type based on plugin characteristics."""
        plugin = device_info.plugin

        # Memory is special: all agents share the same device ID
        if self._is_memory_plugin(plugin):
            return SharedDevicePartitioner(plugin.key)

        # Everything else (CPU, accelerators) uses whole-device assignment
        return WholeDevicePartitioner(plugin.key)

    def _read_manual_assignments(self) -> DeviceAssignments:
        """
        Read device assignments from config for MANUAL mode.

        CPU: count-based allocation, fill from front
        Memory: all agents share the same device
        Accelerators: explicit device IDs from config
        """
        # Pre-sort CPU devices for fill-from-front allocation
        cpu_devices = sorted(
            self.global_devices[self._cpu_device_name].devices, key=lambda d: d.device_id
        )
        cpu_offset = 0

        # Get memory device ID (all agents share this)
        mem_info = self.global_devices[self._mem_device_name]
        mem_devices = list(mem_info.devices)
        if not mem_devices:
            raise ResourceError("No memory devices found. This is a fatal configuration error.")
        mem_device_id = mem_devices[0].device_id

        assignments: dict[AgentId, dict[DeviceName, list[DeviceId]]] = {}

        for agent_config in self.agent_configs:
            allocations = agent_config.resource.allocations
            if allocations is None:
                continue

            agent_id = AgentId(agent_config.agent.defaulted_id)
            assignments[agent_id] = {}

            # CPU: count-based, fill from front
            if allocations.cpu is not None:
                cpu_count = allocations.cpu
                end_idx = min(cpu_offset + cpu_count, len(cpu_devices))
                assignments[agent_id][self._cpu_device_name] = [
                    d.device_id for d in cpu_devices[cpu_offset:end_idx]
                ]
                cpu_offset = end_idx

            # Memory: shared device
            if allocations.mem is not None:
                assignments[agent_id][self._mem_device_name] = [mem_device_id]

            # Accelerators: explicit device IDs from config
            for device_name, device_ids in allocations.devices.items():
                assignments[agent_id][device_name] = list(device_ids)

        return assignments

    def _validate_assignments(self, assignments: DeviceAssignments) -> None:
        """Validate device assignments from MANUAL mode config."""
        # Collect all device IDs per device type across all agents
        all_assignments_by_device: dict[DeviceName, dict[AgentId, Sequence[DeviceId]]] = (
            defaultdict(dict)
        )
        for agent_id, agent_assignments in assignments.items():
            for device_name, device_ids in agent_assignments.items():
                all_assignments_by_device[device_name][agent_id] = device_ids

        for device_name, agent_device_assignments in all_assignments_by_device.items():
            self._validate_device_names_exist(device_name)
            for device_ids in agent_device_assignments.values():
                self._validate_device_ids_exist(device_name, device_ids)
            self._validate_device_mutual_exclusivity(device_name, agent_device_assignments)
            self._warn_unassigned_devices(device_name, agent_device_assignments)

    def _validate_device_names_exist(self, device_name: DeviceName) -> None:
        """Raises InvalidResourceConfigError if DeviceName doesn't exist."""
        if device_name not in self.global_devices:
            raise InvalidResourceConfigError(f"Unknown device type: {device_name}")

    def _validate_device_ids_exist(
        self,
        device_name: DeviceName,
        device_ids: Sequence[DeviceId],
    ) -> None:
        """Raises InvalidResourceConfigError if any DeviceId doesn't exist."""
        available = {d.device_id for d in self.global_devices[device_name].devices}
        for dev_id in device_ids:
            if dev_id not in available:
                raise InvalidResourceConfigError(
                    f"Device {dev_id} not found in {device_name}. Available: {sorted(available)}"
                )

    def _validate_device_mutual_exclusivity(
        self,
        device_name: DeviceName,
        all_assignments: Mapping[AgentId, Sequence[DeviceId]],
    ) -> None:
        """Raises InvalidResourceConfigError if any device is assigned to multiple agents."""
        # Memory is special - all agents can share the same "root" device ID
        # (Memory plugin: DeviceName="mem", DeviceId="root")
        device_info = self.global_devices[device_name]
        if self._is_memory_plugin(device_info.plugin):
            return

        seen: dict[DeviceId, AgentId] = {}
        for agent_id, device_ids in all_assignments.items():
            for dev_id in device_ids:
                if dev_id in seen:
                    raise InvalidResourceConfigError(
                        f"Device {dev_id} assigned to both {seen[dev_id]} and {agent_id}"
                    )
                seen[dev_id] = agent_id

    def _warn_unassigned_devices(
        self,
        device_name: DeviceName,
        all_assignments: Mapping[AgentId, Sequence[DeviceId]],
    ) -> None:
        """Logs warning for devices not assigned to any agent."""
        # Memory is special - "root" is always assigned to all
        device_info = self.global_devices[device_name]
        if self._is_memory_plugin(device_info.plugin):
            return

        assigned: set[DeviceId] = set()
        for device_ids in all_assignments.values():
            assigned.update(device_ids)

        available = {d.device_id for d in device_info.devices}
        unassigned = available - assigned
        if unassigned:
            log.warning(
                "Devices not assigned to any agent: {}={}",
                device_name,
                sorted(unassigned),
            )

    def _apply_device_assignments(
        self,
        agent_computers: Mapping[AgentId, ComputersMap],
        assignments: DeviceAssignments,
    ) -> Mapping[AgentId, ComputersMap]:
        """
        Apply device assignments to agent computers.

        SHARED CODE for both AUTO_SPLIT and MANUAL modes.

        For most devices (CPU, accelerators):
        - Filter devices to only assigned ones
        - Keep original slot amounts (each device = one slot)

        For memory:
        - All agents share the same device ID
        - Slot AMOUNT must be divided among agents (AUTO_SPLIT)
          or set to configured value (MANUAL)
        - This is why memory needs _calculate_memory_slot_amounts()
        """
        result: dict[AgentId, dict[DeviceName, ComputerContext]] = {}

        log.debug(
            "_apply_device_assignments: assignments={}",
            {
                str(k): {str(dn): [str(d) for d in dv] for dn, dv in v.items()}
                for k, v in assignments.items()
            },
        )

        for agent_id, computers in agent_computers.items():
            agent_assignments = assignments.get(agent_id, {})
            result[agent_id] = {}

            for device_name, ctx in computers.items():
                assigned_ids = set(agent_assignments.get(device_name, []))

                log.debug(
                    "_apply_device_assignments: agent={}, device={}, assigned_ids={}, "
                    "original_device_slots={}",
                    agent_id,
                    device_name,
                    sorted(str(d) for d in assigned_ids),
                    sorted(str(d) for d in ctx.alloc_map.device_slots.keys()),
                )

                # Filter devices to only assigned ones
                filtered_devices = [d for d in ctx.devices if d.device_id in assigned_ids]

                # Build new device_slots with only assigned devices
                # Memory: amounts need to be recalculated (divided for AUTO_SPLIT)
                # Other devices: keep original amounts
                if self._is_memory_plugin(ctx.instance) and assigned_ids:
                    new_amounts = self._calculate_memory_slot_amounts(agent_id)
                    new_device_slots = {
                        dev_id: DeviceSlotInfo(
                            slot_type=ctx.alloc_map.device_slots[dev_id].slot_type,
                            slot_name=ctx.alloc_map.device_slots[dev_id].slot_name,
                            amount=new_amounts[dev_id],
                        )
                        for dev_id in assigned_ids
                        if dev_id in ctx.alloc_map.device_slots
                    }
                else:
                    new_device_slots = {
                        dev_id: slot_info
                        for dev_id, slot_info in ctx.alloc_map.device_slots.items()
                        if dev_id in assigned_ids
                    }

                log.debug(
                    "_apply_device_assignments: agent={}, device={}, new_device_slots={}",
                    agent_id,
                    device_name,
                    {str(k): str(v.amount) for k, v in new_device_slots.items()},
                )

                # Update alloc_map with filtered device slots
                ctx.alloc_map.set_device_slots(new_device_slots)

                result[agent_id][device_name] = ComputerContext(
                    instance=ctx.instance,
                    devices=filtered_devices,
                    alloc_map=ctx.alloc_map,
                )

        return result

    def _calculate_memory_slot_amounts(
        self,
        agent_id: AgentId,
    ) -> dict[DeviceId, Decimal]:
        """
        Calculate memory slot amount for an agent.

        Memory is special: single shared device, amount-based splitting.
        """
        mem_info = self.global_devices[self._mem_device_name]
        mem_devices = list(mem_info.devices)
        if not mem_devices:
            raise ResourceError("No memory devices found. This is a fatal configuration error.")
        device_id = mem_devices[0].device_id
        total_mem = Decimal(sum(d.memory_size for d in mem_devices))

        match self.local_config.resource.allocation_mode:
            case ResourceAllocationMode.SHARED:
                return {device_id: total_mem}

            case ResourceAllocationMode.AUTO_SPLIT:
                per_agent = total_mem / self.num_agents
                return {device_id: per_agent}

            case ResourceAllocationMode.MANUAL:
                # Find agent config and get configured memory
                for cfg in self.agent_configs:
                    if AgentId(cfg.agent.defaulted_id) == agent_id:
                        if cfg.resource.allocations and cfg.resource.allocations.mem:
                            return {device_id: Decimal(cfg.resource.allocations.mem)}
                return {device_id: Decimal(0)}

    def _get_agent_allocated_slots(self, agent_id: AgentId) -> SlotsMap:
        """
        Get allocated slots for an agent by summing up slot amounts from assigned devices.

        The result is capped by available_total_slots (total - system reserved).
        This ensures that reserved_slots correctly reflects what the agent cannot use,
        including system-reserved resources.
        """
        if agent_id not in self.agent_computers:
            raise AgentIdNotFoundError(f"Agent ID {agent_id} not found in computers")

        allocated_slots: dict[SlotName, Decimal] = {}
        for device_name, ctx in self.agent_computers[agent_id].items():
            for device_id, slot_info in ctx.alloc_map.device_slots.items():
                slot_name = slot_info.slot_name
                if slot_name not in allocated_slots:
                    allocated_slots[slot_name] = Decimal(0)
                allocated_slots[slot_name] += slot_info.amount

        # Cap by available_total_slots so reserved_slots correctly includes system reserve
        for slot_name in allocated_slots:
            if slot_name in self.available_total_slots:
                allocated_slots[slot_name] = min(
                    allocated_slots[slot_name], self.available_total_slots[slot_name]
                )

        return allocated_slots

    @cached_property
    def _agent_discovery(self) -> AbstractAgentDiscovery:
        backend = self.local_config.agent_common.backend
        return get_agent_discovery(backend)

    async def _load_resources(self) -> Mapping[DeviceName, AbstractComputePlugin]:
        return await self._agent_discovery.load_resources(
            self.etcd,
            self.local_config.model_dump(by_alias=True),
        )

    async def _scan_available_resources(self) -> Mapping[SlotName, Decimal]:
        return await self._agent_discovery.scan_available_resources({
            name: device_info.plugin for name, device_info in self.global_devices.items()
        })


class ComputePluginContext(BasePluginContext[AbstractComputePlugin]):
    plugin_group = "backendai_accelerator_v21"

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: Optional[set[str]] = None,
        blocklist: Optional[set[str]] = None,
    ) -> Iterator[tuple[str, type[AbstractComputePlugin]]]:
        scanned_plugins = [*super().discover_plugins(plugin_group, allowlist, blocklist)]

        def accel_lt_intrinsic(item: tuple[str, type[AbstractComputePlugin]]) -> int:
            # push back "intrinsic" plugins (if exists)
            if item[0] in ("cpu", "mem"):
                return 0
            return -1

        scanned_plugins.sort(key=accel_lt_intrinsic)
        yield from scanned_plugins

    def attach_intrinsic_device(self, plugin: AbstractComputePlugin) -> None:
        self.plugins[plugin.key] = plugin


@attrs.define(auto_attribs=True, slots=True)
class Mount:
    type: MountTypes
    source: Optional[Path]
    target: Path
    permission: MountPermission = MountPermission.READ_ONLY
    opts: Optional[Mapping[str, Any]] = None

    def __str__(self) -> str:
        return f"{self.source}:{self.target}:{self.permission.value}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        source_str, target_str, perm_str = s.split(":")
        source_path = Path(source_str)
        type = MountTypes.BIND
        source: Optional[Path]
        if not source_path.is_absolute():
            if len(source_path.parts) == 1:
                source = Path(source_str)
                type = MountTypes.VOLUME
            else:
                raise ValueError(
                    "Mount source must be an absolute path if it is not a volume name.", source_path
                )
        else:
            source = source_path
        target = Path(target_str)
        if not target.is_absolute():
            raise ValueError("Mount target must be an absolute path.", target)
        perm = MountPermission(perm_str)
        return cls(type, source, target, perm, None)


async def scan_resource_usage_per_slot(
    kernel_ids: Sequence[KernelId],
    scratch_root: Path,
) -> Mapping[SlotName, Decimal]:
    """
    Fetch the current allocated amounts for each resource slot from
    ``/home/config/resource.txt`` files in the kernel containers managed by this agent.
    """
    slot_allocs: dict[SlotName, Decimal] = defaultdict(lambda: Decimal(0))
    loop = asyncio.get_running_loop()

    def _read_kernel_resource_spec(path: Path) -> None:
        nonlocal slot_allocs
        try:
            resource_spec = KernelResourceSpec.read_from_string(path.read_text())
        except FileNotFoundError:
            # there may be races with container destruction
            return
        if resource_spec is None:
            return
        for raw_slot_name in resource_spec.slots.keys():
            slot_name = SlotName(raw_slot_name)
            slot_allocs[slot_name] += Decimal(resource_spec.slots[slot_name])

    async def _wrap_future(fut: asyncio.Future) -> None:
        # avoid type check failures when a future is directly consumed by a taskgroup
        await fut

    async with asyncio.TaskGroup() as tg:
        for kernel_id in kernel_ids:
            fut = loop.run_in_executor(
                None,
                _read_kernel_resource_spec,
                scratch_root / str(kernel_id) / "config" / "resource.txt",
            )
            tg.create_task(_wrap_future(fut))
    return slot_allocs


async def scan_gpu_alloc_map(
    kernel_ids: Sequence[KernelId], scratch_root: Path
) -> dict[DeviceId, Decimal]:
    """
    Fetch the current allocated amounts for fractional gpu from
    ``/home/config/resource.txt`` files in the kernel containers managed by this agent.
    """

    async def _read_kernel_resource_spec(kernel_id: KernelId) -> dict[DeviceId, Decimal]:
        path = scratch_root / str(kernel_id) / "config" / "resource.txt"
        alloc_map: dict[DeviceId, Decimal] = defaultdict(lambda: Decimal(0))

        try:
            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(None, path.read_text)
            resource_spec = KernelResourceSpec.read_from_string(content)

            if cuda := resource_spec.allocations.get(DeviceName("cuda")):
                if cuda_shares := cuda.get(SlotName("cuda.shares")):
                    for device_id, shares in cuda_shares.items():
                        alloc_map[device_id] += Decimal(shares)

                if cuda_device := cuda.get(SlotName("cuda.device")):
                    for device_id, device in cuda_device.items():
                        alloc_map[device_id] += Decimal(device)

        except FileNotFoundError:
            return {}

        except Exception as e:
            setattr(e, "kernel_id", kernel_id)
            raise

        return alloc_map

    tasks = [
        asyncio.create_task(
            _read_kernel_resource_spec(kernel_id),
        )
        for kernel_id in kernel_ids
    ]

    gpu_alloc_map: dict[DeviceId, Decimal] = defaultdict(lambda: Decimal(0))

    for task in asyncio.as_completed(tasks):
        try:
            alloc_map = await task
        except Exception as e:
            kernel_id = getattr(e, "kernel_id", "(unknown)")
            log.error(
                f"GPU alloc map scanning for kernel_id '{kernel_id}' resulted in exception: {e}"
            )
            break

        for device_id, alloc in alloc_map.items():
            gpu_alloc_map[device_id] += alloc

    return gpu_alloc_map


def allocate(
    computers: Mapping[DeviceName, ComputerContext],
    resource_spec: KernelResourceSpec,
    alloc_order: Sequence[DeviceName],
    affinity_map: AffinityMap,
    affinity_policy: AffinityPolicy,
    *,
    allow_fractional_resource_fragmentation: bool = True,
) -> None:
    """
    Updates the allocation maps of the given computer contexts by allocating the given resource spec.
    If it fails, the entire modification of allocation maps is rolled back to the initial state.
    """
    slots = resource_spec.slots

    # Sort out the device names in the resource spec based on the configured allocation order
    dev_names: set[DeviceName] = set()
    for raw_slot_name in slots.keys():
        dev_name = raw_slot_name.split(".", maxsplit=1)[0]
        dev_names.add(DeviceName(dev_name))
    ordered_dev_names = sorted(dev_names, key=lambda item: alloc_order.index(item))

    affinity_hint = AffinityHint(
        None,
        affinity_map,
        affinity_policy,
    )
    current_dev_alloc_maps = {
        dev_name: copy.deepcopy(computers[dev_name].alloc_map.allocations)
        for dev_name in ordered_dev_names
    }

    try:
        for dev_name in ordered_dev_names:
            computer_ctx = computers[dev_name]
            device_id_map = {device.device_id: device for device in computer_ctx.devices}
            device_specific_slots = {
                SlotName(raw_slot_name): Decimal(alloc)
                for raw_slot_name, alloc in slots.items()
                if raw_slot_name == dev_name or raw_slot_name.startswith(f"{dev_name}.")
            }
            try:
                if isinstance(computer_ctx.alloc_map, FractionAllocMap):
                    resource_spec.allocations[dev_name] = computer_ctx.alloc_map.allocate(
                        device_specific_slots,
                        affinity_hint=affinity_hint,
                        context_tag=dev_name,
                        allow_resource_fragmentation=allow_fractional_resource_fragmentation,
                    )
                else:
                    resource_spec.allocations[dev_name] = computer_ctx.alloc_map.allocate(
                        device_specific_slots,
                        affinity_hint=affinity_hint,
                        context_tag=dev_name,
                    )
                log.debug(
                    "allocated {} for device {}",
                    resource_spec.allocations[dev_name],
                    dev_name,
                )
                hint_devices: list[AbstractComputeDevice] = []
                for slot_name, per_device_alloc in resource_spec.allocations[dev_name].items():
                    hint_devices.extend(device_id_map[k] for k in per_device_alloc.keys())
                affinity_hint = AffinityHint(hint_devices, affinity_map, affinity_hint.policy)
            except ResourceError as e:  # including InsufficientResource
                alloc_failure_log_fmt = "\n".join([
                    "resource allocation failed: {0}",
                    "(before allocation) device-specific slots ({1}):\n{2}",
                    "(before allocation) allocation map ({1}):\n{3}",
                ])
                log.info(
                    alloc_failure_log_fmt,
                    e,
                    dev_name,
                    textwrap.indent(pprint.pformat(dict(device_specific_slots)), "  "),
                    textwrap.indent(pprint.pformat(dict(current_dev_alloc_maps[dev_name])), "  "),
                )
                raise
    except ResourceError:
        # rollback the entire allocations in all devices
        for dev in ordered_dev_names:
            computers[dev].alloc_map.allocations = current_dev_alloc_maps[dev]
        raise


def align_memory(orig: int, reserved: int, *, align: int) -> tuple[int, int]:
    """
    Calculate the usable/reserved memory sizes based on the given original size,
    the desired reserved space size, and the alignment.

    The alignment differences are absorbed by the reserved space, so the
    calculated reserved space may differ from the given input.
    """
    if orig % align != 0:
        usable = orig + (orig % align)
    else:
        usable = orig
    usable = usable - reserved
    usable -= usable % align
    actual_reserved = orig - usable
    return usable, actual_reserved
