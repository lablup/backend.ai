import logging
from collections.abc import Mapping, MutableMapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

import aiofiles

from ai.backend.agent.errors import InitializationError
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputePluginContext,
    KernelResourceSpec,
    known_slot_types,
)
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_HOST_CONFIG_FIELD: Final[str] = "HostConfig"
_MOUNTS_FIELD: Final[str] = "Mounts"
_MOUNT_TARGET_FIELD: Final[str] = "Target"
_MOUNT_DESTINATION_FIELD: Final[str] = "Destination"
_MOUNT_SOURCE_FIELD: Final[str] = "Source"


async def load_resources(
    etcd: AbstractKVStore,
    local_config: Mapping[str, Any],
) -> Mapping[DeviceName, AbstractComputePlugin]:
    compute_device_types: MutableMapping[DeviceName, AbstractComputePlugin] = {}

    # Initialize intrinsic plugins by ourselves.
    from .intrinsic import CPUPlugin, MemoryPlugin

    compute_plugin_ctx = ComputePluginContext(
        etcd,
        local_config,
    )
    await compute_plugin_ctx.init(
        allowlist=local_config["agent"]["allow-compute-plugins"],
        blocklist=local_config["agent"]["block-compute-plugins"],
    )
    if "cpu" not in compute_plugin_ctx.plugins:
        cpu_config = await etcd.get_prefix("config/plugins/cpu")
        cpu_plugin = CPUPlugin(cpu_config, local_config)
        await cpu_plugin.init()
        compute_plugin_ctx.attach_intrinsic_device(cpu_plugin)
    if "mem" not in compute_plugin_ctx.plugins:
        memory_config = await etcd.get_prefix("config/plugins/memory")
        memory_plugin = MemoryPlugin(memory_config, local_config)
        await memory_plugin.init()
        compute_plugin_ctx.attach_intrinsic_device(memory_plugin)
    for plugin_name, plugin_instance in compute_plugin_ctx.plugins.items():
        if not all(
            (invalid_name := sname, sname.startswith(f"{plugin_instance.key}."))[1]
            for sname, _ in plugin_instance.slot_types
            if sname not in {"cpu", "mem"}
        ):
            raise InitializationError(
                "Slot types defined by an accelerator plugin must be prefixed by the plugin's key. "
                f"(invalid slot: {invalid_name!r}, plugin key: {plugin_instance.key!r})"
            )
        if plugin_instance.key in compute_device_types:
            raise InitializationError(
                f"A plugin defining the same key '{plugin_instance.key}' already exists. "
                "You may need to uninstall it first."
            )
        compute_device_types[plugin_instance.key] = plugin_instance

    return compute_device_types


async def scan_available_resources(
    compute_device_types: Mapping[DeviceName, AbstractComputePlugin],
) -> Mapping[SlotName, Decimal]:
    slots: MutableMapping[SlotName, Decimal] = {}
    for key, computer in compute_device_types.items():
        known_slot_types.update(computer.slot_types)  # type: ignore  # (only updated here!)
        resource_slots = await computer.available_slots()
        for sname, sval in resource_slots.items():
            slots[sname] = Decimal(sval)
            if slots[sname] <= 0 and sname in (SlotName("cpu"), SlotName("mem")):
                raise InitializationError(
                    f"The resource slot '{sname}' is not sufficient (zero or below zero). "
                    "Try to adjust the reserved resources or use a larger machine."
                )
    return slots


def _get_container_mounts(container_info: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    host_config_mounts: Sequence[Mapping[str, Any]] | None
    try:
        host_config_mounts = container_info[_HOST_CONFIG_FIELD][_MOUNTS_FIELD]
    except KeyError:
        host_config_mounts = None
    if host_config_mounts:
        return host_config_mounts

    mounts: Sequence[Mapping[str, Any]] | None
    try:
        mounts = container_info[_MOUNTS_FIELD]
    except KeyError:
        mounts = None
    return mounts or []


def _get_mount_target(mount: Mapping[str, Any]) -> str | None:
    return mount.get(_MOUNT_TARGET_FIELD) or mount.get(_MOUNT_DESTINATION_FIELD)


async def get_resource_spec_from_container(
    container_info: Mapping[str, Any],
) -> KernelResourceSpec | None:
    for mount in _get_container_mounts(container_info):
        if _get_mount_target(mount) == "/home/config":
            async with aiofiles.open(Path(mount[_MOUNT_SOURCE_FIELD]) / "resource.txt") as f:
                return await KernelResourceSpec.aread_from_file(f)
    return None
