from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Annotated

from pydantic import Field

from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    BackendAISchema,
    ContainerId,
    DeviceId,
    DeviceName,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceSlot,
    ResourceSlotEntry,
    ServicePortProtocols,
    SlotName,
)

__all__ = (
    "AttachedDeviceData",
    "DeviceCapacityData",
    "KernelCreationInfo",
    "KernelResourceSpecData",
    "MountData",
    "ServicePortData",
)


class DeviceCapacityData(BackendAISchema):
    mem: int | None = None
    proc: int | None = None


class AttachedDeviceData(BackendAISchema):
    device_id: DeviceId
    model_name: str
    data: DeviceCapacityData = Field(default_factory=DeviceCapacityData)


class ServicePortData(BackendAISchema):
    name: str
    protocol: ServicePortProtocols
    container_ports: list[int] = Field(default_factory=list)
    host_ports: list[int | None] = Field(default_factory=list)
    is_inference: bool = False


class MountData(BackendAISchema):
    """
    A mount as the agent realized it on the container.

    Mirrors the agent's `Mount`, minus the container-runtime `opts` it never carries on
    a resource spec.
    """

    type: MountTypes
    source: Path | None
    target: Path
    permission: MountPermission


type AllocationAmount = Annotated[
    Decimal,
    # An unbounded allocation is expressed as `Decimal("Infinity")`, which the default
    # `Decimal` constraint rejects. It survives the wire as the string "Infinity".
    Field(allow_inf_nan=True),
]


class KernelResourceSpecData(BackendAISchema):
    """
    The agent's resource spec for one kernel.
    """

    slots: list[ResourceSlotEntry] = Field(default_factory=list)
    allocations: dict[DeviceName, dict[ResourceSlotName, dict[DeviceId, AllocationAmount]]] = Field(
        default_factory=dict
    )
    scratch_disk_size: int = 0
    mounts: list[MountData] = Field(default_factory=list)
    unified_devices: list[tuple[DeviceName, ResourceSlotName]] = Field(default_factory=list)

    def to_resource_slot(self) -> ResourceSlot:
        """
        Sum the per-device allocations into the resource slot the manager accounts by.

        A slot holding no device allocation is left out rather than recorded as zero,
        which is the distinction a caller reading the result back as occupancy depends
        on.
        """
        slots = ResourceSlot()
        for alloc_map in self.allocations.values():
            for slot_name, allocation_by_device in alloc_map.items():
                if not allocation_by_device:
                    continue
                total = sum(allocation_by_device.values(), Decimal(0))
                slots[SlotName(slot_name)] = str(total)
        return slots


class KernelCreationInfo(BackendAISchema):
    """
    What the agent reports about a kernel once its container is up.
    """

    id: KernelId
    container_id: ContainerId
    kernel_host: str
    repl_in_port: int
    repl_out_port: int
    stdin_port: int
    stdout_port: int
    resource_group: ResourceGroupName
    agent_addr: str
    service_ports: list[ServicePortData] = Field(default_factory=list)
    resource_spec: KernelResourceSpecData = Field(default_factory=KernelResourceSpecData)
    attached_devices: dict[DeviceName, list[AttachedDeviceData]] = Field(default_factory=dict)
