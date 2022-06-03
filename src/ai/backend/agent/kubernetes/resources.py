from decimal import Decimal
import logging
from pathlib import Path
from typing import (
    Any, Optional,
    Mapping, MutableMapping,
    Tuple,
)

import aiofiles

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    DeviceName, SlotName,
)
from ..exception import InitializationError
from ..resources import (
    AbstractComputePlugin, ComputePluginContext, KernelResourceSpec, known_slot_types,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


async def detect_resources(
    etcd: AsyncEtcd,
    local_config: Mapping[str, Any],
) -> Tuple[Mapping[DeviceName, AbstractComputePlugin],
           Mapping[SlotName, Decimal]]:
    """
    Detect available computing resource of the system.
    It also loads the accelerator plugins.

    limit_cpus, limit_gpus are deprecated.
    """
    reserved_slots = {
        'cpu':  local_config['resource']['reserved-cpu'],
        'mem':  local_config['resource']['reserved-mem'],
        'disk': local_config['resource']['reserved-disk'],
    }
    slots: MutableMapping[SlotName, Decimal] = {}

    compute_device_types: MutableMapping[DeviceName, AbstractComputePlugin] = {}

    # Initialize intrinsic plugins by ourselves.
    from .intrinsic import CPUPlugin, MemoryPlugin
    compute_plugin_ctx = ComputePluginContext(
        etcd, local_config,
    )
    await compute_plugin_ctx.init()
    if 'cpu' not in compute_plugin_ctx.plugins:
        cpu_config = await etcd.get_prefix('config/plugins/cpu')
        cpu_plugin = CPUPlugin(cpu_config, local_config)
        compute_plugin_ctx.attach_intrinsic_device(cpu_plugin)
    if 'mem' not in compute_plugin_ctx.plugins:
        memory_config = await etcd.get_prefix('config/plugins/memory')
        memory_plugin = MemoryPlugin(memory_config, local_config)
        compute_plugin_ctx.attach_intrinsic_device(memory_plugin)
    for plugin_name, plugin_instance in compute_plugin_ctx.plugins.items():
        if not all(
            (invalid_name := sname, sname.startswith(f'{plugin_instance.key}.'))[1]
            for sname, _ in plugin_instance.slot_types
            if sname not in {'cpu', 'mem'}
        ):
            raise InitializationError(
                "Slot types defined by an accelerator plugin must be prefixed "
                "by the plugin's key.",
                invalid_name,   # noqa: F821
                plugin_instance.key,
            )
        if plugin_instance.key in compute_device_types:
            raise InitializationError(
                f"A plugin defining the same key '{plugin_instance.key}' already exists. "
                "You may need to uninstall it first.")
        compute_device_types[plugin_instance.key] = plugin_instance

    for key, computer in compute_device_types.items():
        known_slot_types.update(computer.slot_types)  # type: ignore  # (only updated here!)
        resource_slots = await computer.available_slots()
        for sname, sval in resource_slots.items():
            slots[sname] = Decimal(max(0, sval - reserved_slots.get(sname, 0)))
            if slots[sname] <= 0 and sname in (SlotName('cpu'), SlotName('mem')):
                raise InitializationError(
                    f"The resource slot '{sname}' is not sufficient (zero or below zero). "
                    "Try to adjust the reserved resources or use a larger machine.")

    log.info('Resource slots: {!r}', slots)
    log.info('Slot types: {!r}', known_slot_types)
    return compute_device_types, slots


async def get_resource_spec_from_container(container_info) -> Optional[KernelResourceSpec]:
    for mount in container_info['HostConfig']['Mounts']:
        if mount['Target'] == '/home/config':
            async with aiofiles.open(Path(mount['Source']) / 'resource.txt', 'r') as f:  # type: ignore
                return await KernelResourceSpec.aread_from_file(f)
    else:
        return None
