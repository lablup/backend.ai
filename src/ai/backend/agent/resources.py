from __future__ import annotations

import asyncio
import copy
import logging
import pprint
import re
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
    Final,
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
from .stats import (
    ContainerMeasurement,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from .types import (
    AbstractAgentDiscovery,
    MountInfo,
    get_agent_discovery,
)
from .types import Container as SessionContainer

if TYPE_CHECKING:
    from io import TextIOWrapper

    from aiofiles.threadpool.text import AsyncTextIOWrapper


type DeviceAllocation = Mapping[SlotName, Mapping[DeviceId, Decimal]]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
known_slot_types: Mapping[SlotName, SlotTypes] = {}

_SHARED_DEVICE_NAMES: Final = frozenset({DeviceName("mem")})

# Regex pattern for natural sort key extraction
_NATURAL_SORT_PATTERN: Final = re.compile(r"(\d+)")


def _natural_sort_key(device_id: DeviceId) -> tuple[str | int, ...]:
    """
    Generate a sort key for natural ordering of device IDs.

    Handles numeric suffixes correctly so that 'cuda10' sorts after 'cuda2'
    instead of between 'cuda1' and 'cuda2' (lexicographic order).
    """

    parts: list[str | int] = []
    for part in _NATURAL_SORT_PATTERN.split(str(device_id)):
        if part.isdigit():
            parts.append(int(part))
        else:
            parts.append(part)
    return tuple(parts)


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
        text = "\n".join(await file.readlines())
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
    _device_name: DeviceName | None
    numa_node: int | None  # NUMA node ID (None if not applicable)

    def __init__(
        self,
        device_id: DeviceId,
        hw_location: str,
        memory_size: int,
        processing_units: int,
        numa_node: int | None = None,
        device_name: DeviceName | None = None,
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


@dataclass(kw_only=True, frozen=True)
class GlobalDeviceInfo:
    """
    Represents the complete view of all physical devices discovered from a compute plugin.

    "Global" refers to the host-wide, shared pool of devices before any partitioning
    or allocation to individual agents. In multi-agent scenarios, GlobalDeviceInfo
    holds all available devices on the host, while each agent receives its own
    ComputerContext with a partitioned subset or view of these devices based on
    the configured allocation mode (SHARED, AUTO_SPLIT, or MANUAL).

    This separation enables:
    - Device discovery to happen once at startup
    - Flexible partitioning strategies to be applied afterward
    - Clear distinction between physical resources and agent-specific allocations
    """

    plugin: AbstractComputePlugin
    devices: Sequence[AbstractComputeDevice]
    alloc_map: AbstractAllocMap

    @property
    def device_ids(self) -> Sequence[DeviceId]:
        return [device.device_id for device in self.devices]


type GlobalDeviceMap = Mapping[DeviceName, GlobalDeviceInfo]
type ComputersMap = Mapping[DeviceName, ComputerContext]
type SlotsMap = Mapping[SlotName, Decimal]


@dataclass(frozen=True)
class DevicePartition:
    device_ids: Sequence[DeviceId]


@dataclass(frozen=True)
class SlotPartition:
    slots: SlotsMap


type Partition = DevicePartition | SlotPartition
type ResourceAssignments = Mapping[AgentId, Mapping[DeviceName, Partition]]


class ResourcePartitioner:
    @classmethod
    def generate_shared_assignments(
        cls,
        global_devices: GlobalDeviceMap,
    ) -> ResourceAssignments:
        def generate_assignment() -> Mapping[DeviceName, Partition]:
            return {
                device_name: DevicePartition(device_ids=device_info.device_ids)
                for device_name, device_info in global_devices.items()
            }

        return defaultdict(generate_assignment)

    @classmethod
    def generate_autosplit_assignments(
        cls,
        global_devices: GlobalDeviceMap,
        agent_ids: Sequence[AgentId],
        available_slots: SlotsMap,
    ) -> ResourceAssignments:
        assignments: dict[AgentId, dict[DeviceName, Partition]] = defaultdict(dict)

        for device_name, device_info in global_devices.items():
            partitions: Mapping[AgentId, Partition]
            if device_name in _SHARED_DEVICE_NAMES:
                partitions = cls._calculate_slot_partitions(device_info, agent_ids, available_slots)
            else:
                partitions = cls._calculate_device_partitions(device_info.device_ids, agent_ids)

            for agent_id, partition in partitions.items():
                assignments[agent_id][device_name] = partition

        return assignments

    @classmethod
    def _calculate_device_partitions(
        cls,
        device_ids: Sequence[DeviceId],
        agent_ids: Sequence[AgentId],
    ) -> Mapping[AgentId, DevicePartition]:
        """
        Assign whole devices to agents using fill-from-front distribution.

        Each device is assigned to exactly one agent. Devices are distributed
        as evenly as possible, with earlier agents receiving extra devices
        when the count does not divide evenly.

        The algorithm divides N devices among M agents as follows:
        - q, r = divmod(N, M)
        - First r agents get (q + 1) devices each
        - Remaining (M - r) agents get q devices each
        """
        sorted_devices = sorted(device_ids, key=_natural_sort_key)
        n_devices = len(sorted_devices)
        n_agents = len(agent_ids)

        q, r = divmod(n_devices, n_agents)

        assignments: dict[AgentId, DevicePartition] = {}
        device_index = 0

        for i, agent_id in enumerate(agent_ids):
            count = q + 1 if i < r else q
            assigned = sorted_devices[device_index : device_index + count]
            assignments[agent_id] = DevicePartition(device_ids=assigned)
            device_index += count

        return assignments

    @classmethod
    def _calculate_slot_partitions(
        cls,
        device_info: GlobalDeviceInfo,
        agent_ids: Sequence[AgentId],
        available_slots: SlotsMap,
    ) -> Mapping[AgentId, SlotPartition]:
        """
        Divide slot amounts among agents for shared devices.

        For FractionAllocMap: simple division (fractional amounts allowed)
        For DiscretePropertyAllocMap: divmod with remainder distribution
          (first agents get extra slots when total doesn't divide evenly)
        """
        num_agents = len(agent_ids)
        device_slot_names = {slot_name for slot_name, _ in device_info.plugin.slot_types}

        result: dict[AgentId, SlotPartition] = {}
        for agent_idx, agent_id in enumerate(agent_ids):
            per_agent_slots: dict[SlotName, Decimal] = {}
            for slot_name in device_slot_names:
                if slot_name not in available_slots:
                    continue

                total_amount = available_slots[slot_name]
                match device_info.alloc_map.get_allocation_type():
                    case alloc_map_mod.AllocationType.FRACTIONAL:
                        per_agent_slots[slot_name] = total_amount / num_agents
                    case alloc_map_mod.AllocationType.DISCRETE:
                        base, remainder = divmod(total_amount, num_agents)
                        extra = Decimal(1) if agent_idx < remainder else Decimal(0)
                        per_agent_slots[slot_name] = base + extra

            result[agent_id] = SlotPartition(slots=per_agent_slots)

        return result

    @classmethod
    def generate_manual_assignments(
        cls,
        global_devices: GlobalDeviceMap,
    ) -> ResourceAssignments:
        # TODO(BA-4146): Implement manual assignment parsing
        return cls.generate_shared_assignments(global_devices)


class ResourceAllocator(aobject):
    local_config: AgentUnifiedConfig
    etcd: AsyncEtcd
    agent_configs: Sequence[AgentUnifiedConfig]

    computers: ComputersMap
    available_total_slots: SlotsMap

    agent_computers: Mapping[AgentId, ComputersMap]
    agent_reserved_slots: Mapping[AgentId, SlotsMap]
    agent_resource_scaling_factor: Mapping[AgentId, SlotsMap]

    @property
    def num_agents(self) -> int:
        return len(self.agent_configs)

    @property
    def agent_ids(self) -> Sequence[AgentId]:
        return [AgentId(cfg.agent.defaulted_id) for cfg in self.agent_configs]

    def __init__(self, local_config: AgentUnifiedConfig, etcd: AsyncEtcd) -> None:
        self.local_config = local_config
        self.etcd = etcd
        self.agent_configs = local_config.get_agent_configs()

    async def __ainit__(self) -> None:
        alloc_map_mod.log_alloc_map = self.local_config.debug.log_alloc_map
        plugins = await self._load_resources()
        global_devices = await self._create_global_devices(plugins)
        self.computers = self._create_computers(global_devices)

        total_slots = await self._calculate_total_slots()
        self.available_total_slots = self._calculate_available_total_slots(total_slots)

        allocation_mode = self.local_config.resource.allocation_mode
        resource_assignments = self._generate_resource_assignments(global_devices)

        agent_computers = {}
        agent_reserved_slots = {}
        agent_resource_scaling_factor = {}
        for agent_id in self.agent_ids:
            agent_assignments = resource_assignments[agent_id]
            agent_computer = await self._apply_resource_assignments(
                agent_assignments, global_devices
            )

            agent_computers[agent_id] = agent_computer
            agent_reserved_slots[agent_id] = self._calculate_reserved_slots(
                agent_computer, total_slots
            )
            agent_resource_scaling_factor[agent_id] = self._calculate_scaling_factors(
                allocation_mode, agent_computer
            )

        self.agent_computers = agent_computers
        self.agent_reserved_slots = agent_reserved_slots
        self.agent_resource_scaling_factor = agent_resource_scaling_factor

    async def __aexit__(self, *exc_info: Any) -> None:
        for _, computer in self.computers.items():
            try:
                await computer.instance.cleanup()
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

    async def _create_global_devices(
        self,
        plugins: Mapping[DeviceName, AbstractComputePlugin],
    ) -> GlobalDeviceMap:
        global_devices: dict[DeviceName, GlobalDeviceInfo] = {}
        for device_name, plugin in plugins.items():
            devices = await plugin.list_devices()
            alloc_map = await plugin.create_alloc_map()
            global_devices[device_name] = GlobalDeviceInfo(
                plugin=plugin,
                devices=list(devices),
                alloc_map=alloc_map,
            )
        return global_devices

    def _create_computers(self, global_devices: GlobalDeviceMap) -> ComputersMap:
        computers: dict[DeviceName, ComputerContext] = {}
        for device_name, device_info in global_devices.items():
            computers[device_name] = ComputerContext(
                instance=device_info.plugin,
                devices=device_info.devices,
                alloc_map=device_info.alloc_map,
            )
        return computers

    async def _calculate_total_slots(self) -> SlotsMap:
        total_slots: dict[SlotName, Decimal] = defaultdict(lambda: Decimal("0"))
        for ctx in self.computers.values():
            plugin_slots = await ctx.instance.available_slots()
            for slot_name, amount in plugin_slots.items():
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

    def _generate_resource_assignments(
        self,
        global_devices: GlobalDeviceMap,
    ) -> ResourceAssignments:
        if len(self.agent_ids) <= 1:
            return ResourcePartitioner.generate_shared_assignments(global_devices)

        allocation_mode = self.local_config.resource.allocation_mode
        match allocation_mode:
            case ResourceAllocationMode.SHARED:
                return ResourcePartitioner.generate_shared_assignments(global_devices)
            case ResourceAllocationMode.AUTO_SPLIT:
                return ResourcePartitioner.generate_autosplit_assignments(
                    global_devices, self.agent_ids, self.available_total_slots
                )
            case ResourceAllocationMode.MANUAL:
                return ResourcePartitioner.generate_manual_assignments(global_devices)

    async def _apply_resource_assignments(
        self,
        device_assignments: Mapping[DeviceName, Partition],
        global_device_map: GlobalDeviceMap,
    ) -> ComputersMap:
        agent_computers: dict[DeviceName, ComputerContext] = {}

        for device_name, device_info in global_device_map.items():
            partition = device_assignments[device_name]
            alloc_map = await device_info.plugin.create_alloc_map()
            assigned_devices: list[AbstractComputeDevice] = []

            match partition:
                case DevicePartition(device_ids=ids):
                    device_ids = set(ids)

                    device_slots_filtered = {
                        device_id: slot_info
                        for device_id, slot_info in alloc_map.device_slots.items()
                        if device_id in device_ids
                    }
                    alloc_map.update_device_slots(device_slots_filtered)

                    assigned_devices = [d for d in device_info.devices if d.device_id in device_ids]

                case SlotPartition(slots=slots_map):
                    device_slots_scaled = {
                        device_id: slot_info
                        if slot_info.slot_name not in slots_map
                        else DeviceSlotInfo(
                            slot_type=slot_info.slot_type,
                            slot_name=slot_info.slot_name,
                            amount=slots_map[slot_info.slot_name],
                        )
                        for device_id, slot_info in alloc_map.device_slots.items()
                    }
                    alloc_map.update_device_slots(device_slots_scaled)

                    assigned_devices = list(device_info.devices)

            agent_computers[device_name] = ComputerContext(
                device_info.plugin,
                assigned_devices,
                alloc_map,
            )

        return agent_computers

    def _calculate_reserved_slots(
        self,
        agent_computers: ComputersMap,
        total_slots: SlotsMap,
    ) -> SlotsMap:
        reserved_slots: dict[SlotName, Decimal] = {}

        agent_slots: dict[SlotName, Decimal] = defaultdict(Decimal)
        for ctx in agent_computers.values():
            for slot_info in ctx.alloc_map.device_slots.values():
                agent_slots[slot_info.slot_name] += slot_info.amount

        for slot_name, total_amount in total_slots.items():
            agent_amount = agent_slots.get(slot_name, Decimal(0))
            available_amount = self.available_total_slots.get(slot_name, total_amount)
            usable_amount = min(agent_amount, available_amount)
            reserved_slots[slot_name] = max(Decimal(0), total_amount - usable_amount)

        return reserved_slots

    def _calculate_scaling_factors(
        self,
        allocation_mode: ResourceAllocationMode,
        agent_computers: Mapping[DeviceName, ComputerContext],
    ) -> SlotsMap:
        num_agents = len(self.agent_ids)

        if num_agents <= 1:
            return defaultdict(lambda: Decimal(1))

        match allocation_mode:
            case ResourceAllocationMode.SHARED:
                return defaultdict(lambda: Decimal(1))

            case ResourceAllocationMode.AUTO_SPLIT | ResourceAllocationMode.MANUAL:
                agent_slots: dict[SlotName, Decimal] = defaultdict(Decimal)
                for ctx in agent_computers.values():
                    for slot_info in ctx.alloc_map.device_slots.values():
                        agent_slots[slot_info.slot_name] += slot_info.amount

                scaling_factors: dict[SlotName, Decimal] = {}
                for slot_name, agent_amount in agent_slots.items():
                    total_amount = self.available_total_slots.get(slot_name, Decimal(0))
                    if total_amount > 0:
                        scaling_factors[slot_name] = agent_amount / total_amount
                    else:
                        scaling_factors[slot_name] = Decimal(0)

                return defaultdict(lambda: Decimal(0), scaling_factors)

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
            name: cctx.instance for name, cctx in self.computers.items()
        })


class ComputePluginContext(BasePluginContext[AbstractComputePlugin]):
    plugin_group = "backendai_accelerator_v21"

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
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
    source: Path | None
    target: Path
    permission: MountPermission = MountPermission.READ_ONLY
    opts: Mapping[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.source}:{self.target}:{self.permission.value}"

    @classmethod
    def from_str(cls, s: str) -> Self:
        source_str, target_str, perm_str = s.split(":")
        source_path = Path(source_str)
        type = MountTypes.BIND
        source: Path | None
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

    async def _wrap_future(fut: asyncio.Future[Any]) -> None:
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
