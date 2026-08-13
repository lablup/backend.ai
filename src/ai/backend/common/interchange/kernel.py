from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import Field

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    BackendAISchema,
    ContainerId,
    DeviceId,
    DeviceName,
    ResourceSlotEntry,
    ServicePortProtocols,
)

__all__ = (
    "AttachedDeviceData",
    "DeviceAllocation",
    "DeviceCapacityData",
    "KernelCreationInfo",
    "PerDeviceAllocation",
    "ServicePortData",
)


type AllocationAmount = Annotated[
    Decimal,
    # An unbounded allocation is expressed as `Decimal("Infinity")`, which the default
    # `Decimal` constraint rejects. It survives the wire as the string "Infinity".
    Field(allow_inf_nan=True),
]

type PerDeviceAllocation = dict[DeviceId, AllocationAmount]
"""How much of one slot each individual device contributed."""

type DeviceAllocation = dict[ResourceSlotName, PerDeviceAllocation]
"""The slots one device type served, and the per-device amounts behind each."""


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


class KernelCreationInfo(BackendAISchema):
    """
    What the agent reports about a kernel once its container is up.

    This is the contract with the manager, not a rendering of the agent's own resource
    spec: it carries the facts the manager records against the kernel and nothing else.
    """

    container_id: ContainerId
    kernel_host: str
    repl_in_port: int
    repl_out_port: int
    service_ports: list[ServicePortData] = Field(default_factory=list)
    attached_devices: dict[DeviceName, list[AttachedDeviceData]] = Field(default_factory=dict)
    allocations: dict[DeviceName, DeviceAllocation] = Field(default_factory=dict)

    def to_resource_slot_entries(self) -> list[ResourceSlotEntry]:
        """
        Sum the per-device allocations into the occupancy the manager accounts by.

        A slot holding no device allocation is left out rather than reported as zero,
        which is the distinction a caller storing the result as occupancy depends on.
        """
        entries: list[ResourceSlotEntry] = []
        for device_allocation in self.allocations.values():
            for slot_name, per_device in device_allocation.items():
                if not per_device:
                    continue
                total = sum(per_device.values(), Decimal(0))
                entries.append(ResourceSlotEntry(resource_type=slot_name, quantity=str(total)))
        return entries
