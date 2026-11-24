from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import (
    BackendAISchema,
    DeviceId,
    DeviceName,
    ResourceSlotEntry,
    SlotName,
    SlotTypes,
)


class AgentInfo(BackendAISchema):
    ip: str
    region: str | None
    scaling_group: str | None
    addr: str
    public_key: PublicKey | None
    public_host: str
    available_resource_slots: list[ResourceSlotEntry]
    slot_key_and_units: dict[ResourceSlotName, SlotTypes]
    version: str
    compute_plugins: dict[DeviceName, dict[str, Any]]
    architecture: str
    auto_terminate_abusing_kernel: bool

    @field_validator("slot_key_and_units", mode="before")
    @classmethod
    def normalize_slot_keys(
        cls, value: dict[str | SlotName, SlotTypes]
    ) -> dict[ResourceSlotName, SlotTypes]:
        """Accept `SlotName` keys from older agent versions, which sent the legacy form."""
        if not isinstance(value, dict):
            raise ValueError("slot_key_and_units must be a dictionary")
        return {ResourceSlotName(str(key)): val for key, val in value.items()}


class KernelGPUAllocation(BackendAISchema):
    """The share of one GPU device that one kernel holds."""

    kernel_id: KernelID
    session_id: SessionID
    allocated_ratio: Decimal = Field(
        description="Allocated amount relative to the capacity of the device (0 to 1)"
    )


class GPUDeviceAllocation(BackendAISchema):
    """One GPU device of an agent and the kernels it is allocated to."""

    device_id: DeviceId
    device_index: int | None = Field(
        description="Index the compute plugin reports for the device, if it reports one"
    )
    allocated_ratio: Decimal = Field(
        description="Sum of the ratios allocated to the kernels (0 if unallocated)"
    )
    kernel_allocations: list[KernelGPUAllocation]
