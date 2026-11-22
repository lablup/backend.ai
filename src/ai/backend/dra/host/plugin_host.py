"""Run one Backend.AI accelerator plugin for the bai-dra driver of its node.

The plugin keeps its Agent-side contract (accelerator plugin v21); this host turns its answers
into ResourceSlice devices and CDI container edits (suggestion-1122 4.5, 4.9).
"""

from __future__ import annotations

import importlib
import logging
import re
import tempfile
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

import aiodocker

from ai.backend.agent.resources import AbstractComputeDevice, AbstractComputePlugin
from ai.backend.common.types import DeviceId, SlotName
from ai.backend.dra.bridge import (
    SHARES_CAPACITY,
    SHARES_PER_DEVICE,
    CapacityPolicy,
    ContainerEdits,
    DeviceInfo,
    DeviceNode,
    DevicesResponse,
    Mount,
)
from ai.backend.dra.errors import (
    PluginLoadError,
    UnknownDeviceError,
    UnsupportedContainerArgsError,
)
from ai.backend.dra.host.isolation import DeviceLimit, HamiCore
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# The docker args a v21 plugin may return that map onto CDI edits.
_SUPPORTED_DOCKER_KEYS: Final = frozenset({"Env", "HostConfig"})
_SUPPORTED_HOST_CONFIG_KEYS: Final = frozenset({"Devices", "Binds", "Mounts", "DeviceRequests"})
_CDI_DRIVER: Final = "cdi"
_RX_NAME: Final = re.compile(r"[^a-z0-9-]+")


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
    _shared: bool
    _isolation: HamiCore | None

    def __init__(
        self,
        plugin: AbstractComputePlugin,
        mount_root: Path | None = None,
        *,
        shared: bool = False,
        isolation: HamiCore | None = None,
    ) -> None:
        self._plugin = plugin
        self._devices = {}
        self._slots = {}
        self._docker = None
        self._mount_root = mount_root or Path(tempfile.gettempdir()) / "bai-dra"
        self._shared = shared
        self._isolation = isolation

    @classmethod
    async def start(
        cls,
        spec: str,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
        mount_root: Path | None = None,
        *,
        shared: bool = False,
        isolation: HamiCore | None = None,
    ) -> PluginHost:
        """`shared` publishes devices that several claims split by `shares` capacity."""
        plugin = load_plugin_class(spec)(plugin_config, local_config)
        await plugin.init()
        log.info("accelerator plugin loaded", plugin=spec, slot_name=str(plugin.key))
        return cls(plugin, mount_root, shared=shared, isolation=isolation)

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

    async def list_devices(self) -> DevicesResponse:
        devices = await self._plugin.list_devices()
        self._devices = {device_name(d.device_id): d for d in devices}
        # The alloc map tells a whole GPU (`cuda.device`) from a MIG instance
        # (`cuda.device:10g-mig`) and the like.
        slot_infos = (await self._plugin.create_alloc_map()).device_slots
        self._slots = {
            name: (
                slot_infos[d.device_id].slot_name if d.device_id in slot_infos else self.device_slot
            )
            for name, d in self._devices.items()
        }
        infos = []
        for name, device in sorted(self._devices.items()):
            attributes: dict[str, str | int | bool] = {
                "slotName": str(self._slots[name]),
                "deviceId": str(device.device_id),
                "hwLocation": device.hw_location,
            }
            if model := getattr(device, "model_name", None):
                attributes["model"] = str(model)
            if device.numa_node is not None:
                attributes["numaNode"] = device.numa_node
            info = DeviceInfo(
                name=name,
                attributes=attributes,
                capacity={
                    "memory": str(int(device.memory_size)),
                    "processingUnits": str(device.processing_units),
                },
            )
            if self._shared:
                # Each share consumes every capacity without a policy in full: only `shares`
                # stays a capacity, the sizes become attributes.
                info.attributes["memory"] = int(device.memory_size)
                info.attributes["processingUnits"] = int(device.processing_units)
                info.capacity = {SHARES_CAPACITY: str(SHARES_PER_DEVICE)}
                info.allow_multiple_allocations = True
                # A request naming no shares takes the whole device.
                info.request_policies[SHARES_CAPACITY] = CapacityPolicy(
                    default=str(SHARES_PER_DEVICE), min="1", max=str(SHARES_PER_DEVICE), step="1"
                )
            infos.append(info)
        return DevicesResponse(slot_name=str(self._plugin.key), devices=infos)

    async def prepare(
        self,
        claim_uid: str,
        names: list[str],
        consumed: Mapping[str, Mapping[str, str]] | None = None,
    ) -> ContainerEdits:
        if not self._devices:
            await self.list_devices()
        unknown = [n for n in names if n not in self._devices]
        if unknown:
            raise UnknownDeviceError(f"devices not on this node: {unknown}")
        alloc: dict[SlotName, dict[DeviceId, Decimal]] = {}
        for n in names:
            alloc.setdefault(self._slots[n], {})[self._devices[n].device_id] = Decimal(1)
        if self._docker is None:
            # v21 plugins take a Docker client for Docker-only queries; it is never connected.
            self._docker = aiodocker.Docker(url="unix:///nonexistent")
        edits = docker_args_to_edits(await self._plugin.generate_docker_args(self._docker, alloc))
        source = self._mount_root / claim_uid
        source.mkdir(parents=True, exist_ok=True)
        for mount in await self._plugin.generate_mounts(source, alloc):
            # The Agent mounts what a plugin generates read-only.
            edits.mounts.append(
                Mount(
                    host_path=str(mount.src_path),
                    container_path=str(mount.dst_path),
                    options=["bind", "ro"],
                )
            )
        if self._isolation is not None:
            limits = self._limits(names, consumed or {})
            if any(limit.shares < SHARES_PER_DEVICE for limit in limits):
                isolation = self._isolation.edits(claim_uid, limits)
                edits.env.extend(isolation.env)
                edits.mounts.extend(isolation.mounts)
        log.debug("claim prepared", claim_uid=claim_uid, devices=",".join(names))
        return edits

    def _limits(
        self, names: list[str], consumed: Mapping[str, Mapping[str, str]]
    ) -> list[DeviceLimit]:
        """In the container's device order (PCI location), as the CUDA runtime numbers them."""
        limits = []
        for name in sorted(names, key=lambda n: self._devices[n].hw_location):
            device = self._devices[name]
            shares = int(consumed.get(name, {}).get(SHARES_CAPACITY, SHARES_PER_DEVICE))
            memory = int(device.memory_size) * shares // SHARES_PER_DEVICE
            limits.append(DeviceLimit(memory_bytes=memory, shares=shares))
        return limits

    async def unprepare(self, claim_uid: str) -> None:
        log.debug("claim unprepared", claim_uid=claim_uid)
