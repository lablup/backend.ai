"""Compute-resource discovery for the containerd backend.

Mirrors `docker/resources.py`: it loads the intrinsic CPU/Memory compute
plugins (and any registered accelerator plugins) and aggregates their
slot capacities. The logic is backend-agnostic — only the intrinsic
plugins it instantiates are containerd-specific (see `.intrinsic`).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping
from decimal import Decimal
from typing import Any, cast

from ai.backend.agent.exception import InitializationError
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputePluginContext,
    known_slot_types,
)
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def load_resources(
    etcd: AbstractKVStore,
    local_config: Mapping[str, Any],
) -> Mapping[DeviceName, AbstractComputePlugin]:
    compute_device_types: MutableMapping[DeviceName, AbstractComputePlugin] = {}

    # Initialize intrinsic plugins by ourselves.
    from .intrinsic import CPUPlugin, MemoryPlugin

    compute_plugin_ctx = ComputePluginContext(etcd, local_config)
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
    for _plugin_name, plugin_instance in compute_plugin_ctx.plugins.items():
        if not all(
            (invalid_name := sname, sname.startswith(f"{plugin_instance.key}."))[1]
            for sname, _ in plugin_instance.slot_types
            if sname not in {"cpu", "mem"}
        ):
            raise InitializationError(
                "Slot types defined by an accelerator plugin must be prefixed by the plugin's key.",
                invalid_name,
                plugin_instance.key,
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
    for _key, computer in compute_device_types.items():
        # `known_slot_types` is a process-wide registry; backends populate it
        # here. cast() drops its read-only typing for this sanctioned update.
        cast("MutableMapping[Any, Any]", known_slot_types).update(computer.slot_types)
        resource_slots = await computer.available_slots()
        for sname, sval in resource_slots.items():
            slots[sname] = Decimal(sval)
            if slots[sname] <= 0 and sname in (SlotName("cpu"), SlotName("mem")):
                raise InitializationError(
                    f"The resource slot '{sname}' is not sufficient (zero or below zero). "
                    "Try to adjust the reserved resources or use a larger machine."
                )
    return slots
