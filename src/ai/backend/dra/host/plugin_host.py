"""Run one Backend.AI accelerator plugin for the bai-dra driver of its node.

The plugin keeps its Agent-side contract (accelerator plugin v21); this host turns its answers
into ResourceSlice devices and CDI container edits (suggestion-1122 4.5, 4.9).
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import re
import shutil
import uuid
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

import aiodocker

from ai.backend.agent.alloc_map import DeviceSlotInfo
from ai.backend.agent.resources import AbstractComputeDevice, AbstractComputePlugin
from ai.backend.common.types import DeviceId, SlotName, SlotTypes
from ai.backend.dra.bridge import (
    SHARE_SCALE,
    SHARES_CAPACITY,
    SHARES_CAPACITY_QUALIFIED,
    CapacityPolicy,
    ContainerEdits,
    DeviceInfo,
    DeviceNode,
    DevicesResponse,
    Mount,
    parse_quantity,
)
from ai.backend.dra.errors import (
    InvalidClaimUIDError,
    InvalidQuantityError,
    IsolationRequiredError,
    MissingConsumedSharesError,
    PluginLoadError,
    UnknownDeviceError,
    UnsupportedContainerArgsError,
)
from ai.backend.dra.host.isolation import (
    DeviceLimit,
    IsolationProvider,
    SharedAllocation,
    limit_from_shares,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# The docker args a v21 plugin may return that map onto CDI edits.
_SUPPORTED_DOCKER_KEYS: Final = frozenset({"Env", "HostConfig"})
_SUPPORTED_HOST_CONFIG_KEYS: Final = frozenset({"Devices", "Binds", "Mounts", "DeviceRequests"})
_CDI_DRIVER: Final = "cdi"
_RX_NAME: Final = re.compile(r"[^a-z0-9-]+")
_RX_CLAIM_UID: Final = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_RX_PCI_BUS_ID: Final = re.compile(r"^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$")
_RX_PCIE_ROOT: Final = re.compile(r"^pci[0-9a-f]{4}:[0-9a-f]{2}$")
# Not a tmpfs of the plugin host: CDI mounts name it on the node, so the chart mounts this
# host path at the same path.
DEFAULT_MOUNT_ROOT: Final = Path("/var/lib/bai-dra/mounts")
STD_PCI_BUS_ID: Final = "resource.kubernetes.io/pciBusID"
STD_PCIE_ROOT: Final = "resource.kubernetes.io/pcieRoot"
STD_NUMA_NODE: Final = "resource.kubernetes.io/numaNode"


def load_plugin_class(spec: str) -> type[AbstractComputePlugin]:
    """`module.path:ClassName`; the dev image carries no entry point metadata."""
    module_name, _, class_name = spec.partition(":")
    try:
        cls = getattr(importlib.import_module(module_name), class_name)
    except (ImportError, AttributeError) as e:
        raise PluginLoadError(f"cannot load accelerator plugin {spec}") from e
    if not (isinstance(cls, type) and issubclass(cls, AbstractComputePlugin)):
        raise PluginLoadError(f"{spec} is not an accelerator plugin")
    return cls


def device_name(device_id: DeviceId) -> str:
    return "dev-" + (_RX_NAME.sub("-", str(device_id).lower()).strip("-") or "0")


def pci_bus_id(hw_location: str) -> str | None:
    """The PCI address of a device whose `hw_location` is one (`0000:3b:00.0`)."""
    bus_id = hw_location.strip().lower()
    return bus_id if _RX_PCI_BUS_ID.match(bus_id) else None


def pcie_root(bus_id: str, sysfs_root: Path) -> str | None:
    """The PCIe root complex (`pci0000:00`) the sysfs device path of `bus_id` hangs under."""
    try:
        resolved = (sysfs_root / "bus/pci/devices" / bus_id).resolve(strict=True)
    except OSError:
        return None
    return next((part for part in resolved.parts if _RX_PCIE_ROOT.match(part)), None)


def share_capacity(memory_size: int, processing_units: int, unit_mem: int, unit_proc: int) -> int:
    """A device's share capacity in 0.01-share units: min(memory, SMs) in shares, rounded down."""
    return min(
        memory_size * SHARE_SCALE // unit_mem,
        processing_units * SHARE_SCALE // unit_proc,
    )


def consumed_shares(consumed: Mapping[str, str]) -> int | None:
    """The `shares` a shared allocation consumed, by the bare or the qualified name."""
    raw = consumed.get(SHARES_CAPACITY, consumed.get(SHARES_CAPACITY_QUALIFIED))
    if raw is None:
        return None
    value = parse_quantity(raw)
    if value != value.to_integral_value():
        raise InvalidQuantityError(f"shares must be a whole number of 0.01-share units: {raw}")
    return int(value)


def docker_args_to_edits(args: Mapping[str, Any]) -> ContainerEdits:
    unknown = set(args) - _SUPPORTED_DOCKER_KEYS
    host_config: Mapping[str, Any] = args.get("HostConfig", {})
    unknown |= {f"HostConfig.{k}" for k in set(host_config) - _SUPPORTED_HOST_CONFIG_KEYS}
    if unknown:
        raise UnsupportedContainerArgsError(
            f"the plugin returned docker args the DRA path cannot express: {sorted(unknown)}"
        )
    edits = ContainerEdits(env=list(args.get("Env", [])))
    for request in host_config.get("DeviceRequests", []):
        # Requests naming CDI devices pass through; other drivers need a Docker daemon.
        if request.get("Driver") != _CDI_DRIVER:
            raise UnsupportedContainerArgsError(
                f"the plugin requested devices through driver {request.get('Driver')!r},"
                " which the DRA path cannot express"
            )
        edits.cdi_devices.extend(request.get("DeviceIDs") or [])
    for device in host_config.get("Devices", []):
        edits.device_nodes.append(
            DeviceNode(
                path=device["PathInContainer"],
                host_path=device["PathOnHost"],
                permissions=device.get("CgroupPermissions"),
            )
        )
    for bind in host_config.get("Binds", []):
        src, dst, *mode = bind.split(":")
        edits.mounts.append(Mount(host_path=src, container_path=dst, options=["bind", *mode]))
    for mount in host_config.get("Mounts", []):
        options = ["bind", "ro" if mount.get("ReadOnly") else "rw"]
        edits.mounts.append(
            Mount(host_path=mount["Source"], container_path=mount["Target"], options=options)
        )
    return edits


class PluginHost:
    _plugin: AbstractComputePlugin
    _devices: dict[str, AbstractComputeDevice]
    _slots: dict[str, SlotName]  # device name → the slot the plugin allocates it by
    _docker: aiodocker.Docker | None
    _mount_root: Path
    _sysfs_root: Path
    _shared: bool
    _isolation: IsolationProvider | None
    _host_id: str
    _generation: int
    _published: list[DeviceInfo] | None

    def __init__(
        self,
        plugin: AbstractComputePlugin,
        mount_root: Path | None = None,
        *,
        shared: bool = False,
        isolation: IsolationProvider | None = None,
        sysfs_root: Path = Path("/sys"),
    ) -> None:
        if shared and isolation is None:
            # Shared devices without a provider would let every claim use the whole device.
            raise IsolationRequiredError("shared devices need an isolation provider")
        self._plugin = plugin
        self._devices = {}
        self._slots = {}
        self._docker = None
        self._mount_root = mount_root or DEFAULT_MOUNT_ROOT
        self._sysfs_root = sysfs_root
        self._shared = shared
        self._isolation = isolation
        self._host_id = uuid.uuid4().hex
        self._generation = 0
        self._published = None

    @classmethod
    async def start(
        cls,
        spec: str,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
        mount_root: Path | None = None,
        *,
        shared: bool = False,
        isolation: IsolationProvider | None = None,
        sysfs_root: Path = Path("/sys"),
    ) -> PluginHost:
        """`shared` publishes devices that several claims split by `shares` capacity."""
        if shared and isolation is None:
            raise IsolationRequiredError("shared devices need an isolation provider")
        plugin = load_plugin_class(spec)(plugin_config, local_config)
        await plugin.init()
        log.info("accelerator plugin loaded", plugin=spec, slot_name=str(plugin.key))
        return cls(plugin, mount_root, shared=shared, isolation=isolation, sysfs_root=sysfs_root)

    async def close(self) -> None:
        await self._plugin.cleanup()
        if self._docker is not None:
            await self._docker.close()

    @property
    def device_slot(self) -> SlotName:
        """The slot a whole device is allocated by (`<key>.device`, or the first one)."""
        names = [name for name, _ in self._plugin.slot_types]
        preferred = SlotName(f"{self._plugin.key}.device")
        return preferred if preferred in names else names[0]

    @property
    def shares_slot(self) -> SlotName:
        """The slot every shared device is allocated by."""
        return SlotName(f"{self._plugin.key}.shares")

    def _pcie_roots(self, devices: Mapping[str, AbstractComputeDevice]) -> dict[str, str]:
        """Device name → PCIe root, read from sysfs."""
        roots = {}
        for name, device in devices.items():
            if (bus_id := pci_bus_id(device.hw_location)) is not None:
                if (root := pcie_root(bus_id, self._sysfs_root)) is not None:
                    roots[name] = root
        return roots

    def _attributes(
        self,
        name: str,
        slot: SlotName,
        device: AbstractComputeDevice,
        pcie_roots: Mapping[str, str],
    ) -> dict[str, str | int | bool]:
        attributes: dict[str, str | int | bool] = {
            "slotName": str(slot),
            "deviceId": str(device.device_id),
            "hwLocation": device.hw_location,
        }
        if model := getattr(device, "model_name", None):
            attributes["model"] = str(model)
        if device.numa_node is not None and device.numa_node >= 0:
            attributes["numaNode"] = device.numa_node
            attributes[STD_NUMA_NODE] = device.numa_node
        if (bus_id := pci_bus_id(device.hw_location)) is not None:
            attributes[STD_PCI_BUS_ID] = bus_id
        if name in pcie_roots:
            attributes[STD_PCIE_ROOT] = pcie_roots[name]
        return attributes

    def _share_capacity(self, device: AbstractComputeDevice) -> int:
        unit_mem, unit_proc = self._plugin.share_units()
        return share_capacity(
            int(device.memory_size), int(device.processing_units), unit_mem, unit_proc
        )

    def _exclusive_slot(self, slot_info: DeviceSlotInfo | None) -> SlotName | None:
        """The slot of a device the plugin never splits (a MIG instance: `cuda.device:1g.10gb-mig`)."""
        if slot_info is None:
            return None
        if slot_info.slot_type == SlotTypes.UNIQUE or slot_info.slot_name not in (
            self.device_slot,
            self.shares_slot,
        ):
            return slot_info.slot_name
        return None

    async def list_devices(self) -> DevicesResponse:
        devices = {device_name(d.device_id): d for d in await self._plugin.list_devices()}
        # The alloc map tells a whole GPU (`cuda.device`) from a MIG instance
        # (`cuda.device:10g-mig`) and the like.
        slot_infos = (await self._plugin.create_alloc_map()).device_slots
        slots: dict[str, SlotName] = {}
        for name, d in devices.items():
            slot_info = slot_infos.get(d.device_id)
            exclusive = self._exclusive_slot(slot_info)
            if exclusive is not None:
                slots[name] = exclusive
            elif self._shared:
                slots[name] = self.shares_slot
            else:
                slots[name] = slot_info.slot_name if slot_info is not None else self.device_slot
        if self._shared:
            # A GPU in MIG mode is served by its instances alone, never as a shared device.
            mig_parents = {
                str(mother)
                for name, d in devices.items()
                if slots[name] != self.shares_slot
                and (mother := getattr(d, "mother_uuid", None)) is not None
            }
            for name in [
                n
                for n, d in devices.items()
                if slots[n] == self.shares_slot and str(d.device_id) in mig_parents
            ]:
                del devices[name], slots[name]
        # Both maps change together: a prepare between two awaits sees one generation.
        self._devices, self._slots = devices, slots
        pcie_roots = await asyncio.to_thread(self._pcie_roots, devices)
        infos = []
        for name, device in sorted(devices.items()):
            info = DeviceInfo(
                name=name,
                attributes=self._attributes(name, slots[name], device, pcie_roots),
                capacity={
                    "memory": str(int(device.memory_size)),
                    "processingUnits": str(device.processing_units),
                },
            )
            if slots[name] == self.shares_slot:
                capacity = self._share_capacity(device)
                if capacity < 1:
                    log.warning("device too small for one share unit", device=name)
                    continue
                # Each share consumes every capacity without a policy in full: only `shares`
                # stays a capacity, the sizes become attributes.
                info.attributes["memory"] = int(device.memory_size)
                info.attributes["processingUnits"] = int(device.processing_units)
                info.capacity = {SHARES_CAPACITY: str(capacity)}
                info.allow_multiple_allocations = True
                # A request naming no shares takes the whole device.
                info.request_policies[SHARES_CAPACITY] = CapacityPolicy(
                    default=str(capacity), min="1", max=str(capacity), step="1"
                )
            infos.append(info)
        if infos != self._published:
            self._published = infos
            self._generation += 1
        return DevicesResponse(
            slot_name=str(self._plugin.key),
            host_id=self._host_id,
            generation=self._generation,
            devices=infos,
        )

    def _claim_dir(self, claim_uid: str) -> Path:
        if not _RX_CLAIM_UID.match(claim_uid):
            raise InvalidClaimUIDError(f"not a claim UID: {claim_uid!r}")
        return self._mount_root / claim_uid

    def _shares(
        self, names: list[str], consumed: Mapping[str, Mapping[str, str]]
    ) -> dict[str, int]:
        """The consumed shares of each shared device; a device without them is refused."""
        shares = {}
        for name in names:
            value = consumed_shares(consumed.get(name, {}))
            capacity = self._share_capacity(self._devices[name])
            if value is None or not 1 <= value <= capacity:
                raise MissingConsumedSharesError(
                    f"shared device {name} consumed {value} of {capacity} share units"
                )
            shares[name] = value
        return shares

    def _alloc(
        self, names: list[str], shares: Mapping[str, int]
    ) -> dict[SlotName, dict[DeviceId, Decimal]]:
        alloc: dict[SlotName, dict[DeviceId, Decimal]] = {}
        for n in names:
            slot = self._slots[n]
            amount = Decimal(1)
            if n in shares and str(slot).endswith(".shares"):
                amount = Decimal(shares[n]) / SHARE_SCALE
            alloc.setdefault(slot, {})[self._devices[n].device_id] = amount
        return alloc

    async def _edits(self, alloc: dict[SlotName, dict[DeviceId, Decimal]]) -> ContainerEdits:
        if self._docker is None:
            # v21 plugins take a Docker client for Docker-only queries; it is never connected.
            self._docker = aiodocker.Docker(url="unix:///nonexistent")
        return docker_args_to_edits(await self._plugin.generate_docker_args(self._docker, alloc))

    async def prepare(
        self,
        claim_uid: str,
        names: list[str],
        consumed: Mapping[str, Mapping[str, str]] | None = None,
    ) -> tuple[ContainerEdits, dict[str, list[str]]]:
        """The claim's edits and, per device, the CDI devices of other specs for it alone."""
        source = self._claim_dir(claim_uid)
        if not self._devices:
            await self.list_devices()
        unknown = [n for n in names if n not in self._devices]
        if unknown:
            raise UnknownDeviceError(f"devices not on this node: {unknown}")
        # Everything that reads the device maps runs before the first await: list_devices
        # replaces them meanwhile.
        shared_names = [n for n in names if self._slots[n] == self.shares_slot]
        shares = self._shares(shared_names, consumed or {}) if self._shared else {}
        partial = [n for n in shares if shares[n] < self._share_capacity(self._devices[n])]
        alloc = self._alloc(names, shares)
        singles = {n: self._alloc([n], shares) for n in names}
        limits = self._limits(names, shares) if partial else []
        edits = await self._edits(alloc)
        per_device: dict[str, list[str]] = {}
        if edits.cdi_devices:
            for n in names:
                single = await self._edits(singles[n])
                per_device[n] = [i for i in single.cdi_devices if i in edits.cdi_devices]
            attributed = {i for ids in per_device.values() for i in ids}
            edits.cdi_devices = [i for i in edits.cdi_devices if i not in attributed]
        await asyncio.to_thread(source.mkdir, parents=True, exist_ok=True)
        for mount in await self._plugin.generate_mounts(source, alloc):
            # The Agent mounts what a plugin generates read-only.
            edits.mounts.append(
                Mount(
                    host_path=str(mount.src_path),
                    container_path=str(mount.dst_path),
                    options=["bind", "ro"],
                )
            )
        # A device taken in full needs no isolation; one partial device puts the claim under
        # the provider (fail closed).
        if partial:
            if self._isolation is None:
                raise IsolationRequiredError("shared devices need an isolation provider")
            allocation = SharedAllocation(
                claim_uid=claim_uid,
                claim_dir=source,
                limits=limits,
                alloc=alloc,
            )
            isolation = await self._isolation.edits(allocation, self._plugin)
            edits.env.extend(isolation.env)
            edits.mounts.extend(isolation.mounts)
        log.debug("claim prepared", claim_uid=claim_uid, devices=",".join(names))
        return edits, per_device

    def _limits(self, names: list[str], shares: Mapping[str, int]) -> list[DeviceLimit]:
        """In the container's device order (PCI location), as the CUDA runtime numbers them.
        A device taken in full gets its whole memory and every SM."""
        unit_mem, unit_proc = self._plugin.share_units()
        ordered = sorted(names, key=lambda n: self._devices[n].hw_location)
        limits = []
        for index, name in enumerate(ordered):
            if name not in shares:
                continue
            device = self._devices[name]
            if shares[name] >= self._share_capacity(device):
                limits.append(DeviceLimit(index, int(device.memory_size), 100))
                continue
            limits.append(
                limit_from_shares(
                    index, shares[name], unit_mem, unit_proc, int(device.processing_units)
                )
            )
        return limits

    async def unprepare(self, claim_uid: str) -> None:
        source = self._claim_dir(claim_uid)
        await asyncio.to_thread(shutil.rmtree, source, ignore_errors=True)
        log.debug("claim unprepared", claim_uid=claim_uid)
