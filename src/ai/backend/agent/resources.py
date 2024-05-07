from __future__ import annotations

import asyncio
import copy
import json
import logging
import pprint
import textwrap
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    TextIO,
    Tuple,
    Type,
    cast,
)

import aiodocker
import attrs

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.common.types import (
    AcceleratorMetadata,
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
)

# Expose legacy import names for plugins
from .affinity_map import AffinityHint, AffinityMap, AffinityPolicy
from .alloc_map import AbstractAllocMap as AbstractAllocMap  # noqa: F401
from .alloc_map import AllocationStrategy as AllocationStrategy  # noqa: F401
from .alloc_map import DeviceSlotInfo as DeviceSlotInfo  # noqa: F401
from .alloc_map import DiscretePropertyAllocMap as DiscretePropertyAllocMap  # noqa: F401
from .alloc_map import FractionAllocMap as FractionAllocMap  # noqa: F401
from .exception import ResourceError
from .stats import ContainerMeasurement, NodeMeasurement, ProcessMeasurement, StatContext
from .types import Container as SessionContainer
from .types import MountInfo

if TYPE_CHECKING:
    from io import TextIOWrapper

    from aiofiles.threadpool.text import AsyncTextIOWrapper

    from .agent import ComputerContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

known_slot_types: Mapping[SlotName, SlotTypes] = {}


@attrs.define(slots=True)
class KernelResourceSpec:
    """
    This struct-like object stores the kernel resource allocation information
    with serialization and deserialization.

    It allows seamless reconstruction of allocations even when the agent restarts
    while kernel containers are running.
    """

    container_id: str
    """The container ID to refer inside containers."""

    slots: Mapping[SlotName, str]
    """Stores the original user-requested resource slots."""

    allocations: MutableMapping[DeviceName, Mapping[SlotName, Mapping[DeviceId, Decimal]]]
    """
    Represents the resource allocations for each slot (device) type and devices.
    """

    scratch_disk_size: int
    """The size of scratch disk. (not implemented yet)"""

    mounts: List["Mount"] = attrs.Factory(list)
    """The mounted vfolder list."""

    def freeze(self) -> None:
        """Replace the attribute setter to make it immutable."""
        # TODO: implement
        pass

        # def _frozen_setattr(self, name, value):
        #     raise RuntimeError("tried to modify a frozen KernelResourceSpec object")

        # self.mounts = tuple(self.mounts)  # type: ignore
        # # TODO: wrap slots and allocations with frozendict?
        # setattr(self, '__setattr__', _frozen_setattr)  # <-- __setattr__ is read-only... :(

    def write_to_string(self) -> str:
        mounts_str = ",".join(map(str, self.mounts))
        slots_str = json.dumps({k: str(v) for k, v in self.slots.items()})

        resource_str = f"CID={self.container_id}\n"
        resource_str += f"SCRATCH_SIZE={BinarySize(self.scratch_disk_size):m}\n"
        resource_str += f"MOUNTS={mounts_str}\n"
        resource_str += f"SLOTS={slots_str}\n"

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
    def read_from_string(cls, text: str) -> "KernelResourceSpec":
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
            container_id=kvpairs.get("CID", "unknown"),
            scratch_disk_size=BinarySize.finite_from_str(kvpairs["SCRATCH_SIZE"]),
            allocations=dict(allocations),
            slots=ResourceSlot(json.loads(kvpairs["SLOTS"])),
            mounts=mounts,
        )

    @classmethod
    def read_from_file(cls, file: TextIOWrapper) -> "KernelResourceSpec":
        text = "\n".join(file.readlines())
        return cls.read_from_string(text)

    @classmethod
    async def aread_from_file(cls, file: AsyncTextIOWrapper) -> "KernelResourceSpec":
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
        return json.dumps(self.to_json_serializable_dict())


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
    slot_types: Sequence[Tuple[SlotName, SlotTypes]]
    exclusive_slot_types: Set[str]

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
    async def create_alloc_map(self) -> "AbstractAllocMap":
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
        device_alloc,
    ) -> Mapping[str, Any]:
        """
        When starting a new container, generate device-specific options for the
        docker container create API as a dictionary, referring the given allocation
        map.  The agent will merge it with its own options.
        """
        return {}

    async def generate_resource_data(self, device_alloc) -> Mapping[str, str]:
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
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        """
        Make up container-attached device information with allocated device id.
        """
        return []

    async def get_node_hwinfo(self) -> HardwareMetadata:
        raise NotImplementedError

    @abstractmethod
    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        """
        Returns reference string (e.g. Id, name, ...) of docker networks
        to attach to container for accelerator to work properly.
        """
        return []

    @abstractmethod
    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        """
        Populates additional files/directories under `source_path`
        to mount to container and returns `MountInfo`.
        Agent will then read this `MountInfo`s and mount files/directories.
        """
        return []


class ComputePluginContext(BasePluginContext[AbstractComputePlugin]):
    plugin_group = "backendai_accelerator_v21"

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: set[str] = None,
        blocklist: set[str] = None,
    ) -> Iterator[Tuple[str, Type[AbstractComputePlugin]]]:
        scanned_plugins = [*super().discover_plugins(plugin_group, allowlist, blocklist)]

        def accel_lt_intrinsic(item):
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

    def __str__(self):
        return f"{self.source}:{self.target}:{self.permission.value}"

    @classmethod
    def from_str(cls, s):
        source, target, perm = s.split(":")
        source = Path(source)
        type = MountTypes.BIND
        if not source.is_absolute():
            if len(source.parts) == 1:
                source = str(source)
                type = MountTypes.VOLUME
            else:
                raise ValueError(
                    "Mount source must be an absolute path if it is not a volume name.", source
                )
        target = Path(target)
        if not target.is_absolute():
            raise ValueError("Mount target must be an absolute path.", target)
        perm = MountPermission(perm)
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
        for slot_name in resource_spec.slots.keys():
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


def allocate(
    computers: Mapping[DeviceName, ComputerContext],
    resource_spec: KernelResourceSpec,
    alloc_order: Sequence[DeviceName],
    affinity_map: AffinityMap,
    affinity_policy: AffinityPolicy,
) -> None:
    """
    Updates the allocation maps of the given computer contexts by allocating the given resource spec.
    If it fails, the entire modification of allocation maps is rolled back to the initial state.
    """
    slots = resource_spec.slots

    # Sort out the device names in the resource spec based on the configured allocation order
    dev_names: set[DeviceName] = set()
    for slot_name in slots.keys():
        dev_name = slot_name.split(".", maxsplit=1)[0]
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
                SlotName(slot_name): Decimal(alloc)
                for slot_name, alloc in slots.items()
                if slot_name == dev_name or slot_name.startswith(f"{dev_name}.")
            }
            try:
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
