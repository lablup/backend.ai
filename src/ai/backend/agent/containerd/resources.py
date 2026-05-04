from collections.abc import Mapping, MutableMapping
from decimal import Decimal
from typing import Any

from ai.backend.agent.resources import AbstractComputePlugin
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName


async def load_resources(
    etcd: AbstractKVStore,
    local_config: Mapping[str, Any],
) -> Mapping[DeviceName, AbstractComputePlugin]:
    # TODO(containerd-prototype): mirror docker/resources.load_resources —
    # discover intrinsic CPU/Memory plugins and any accelerator plugins
    # registered for the containerd backend.
    del etcd, local_config
    compute_device_types: MutableMapping[DeviceName, AbstractComputePlugin] = {}
    return compute_device_types


async def scan_available_resources(
    compute_device_types: Mapping[DeviceName, AbstractComputePlugin],
) -> Mapping[SlotName, Decimal]:
    # TODO(containerd-prototype): aggregate slot capacity per loaded plugin.
    del compute_device_types
    slots: MutableMapping[SlotName, Decimal] = {}
    return slots
