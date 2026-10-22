from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.kernel_group import KernelGroupID, KernelGroupRole
from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import FieldData

__all__ = (
    "KernelGroupData",
    "KernelGroupEnvironData",
    "KernelGroupResourceSlotData",
)


@dataclass(frozen=True)
class KernelGroupData(FieldData):
    id: KernelGroupID
    session_id: SessionID
    role: KernelGroupRole
    image_id: ImageID | None
    shmem: int | None
    startup_command: str | None
    preopen_ports: list[int]
    requested_starts_at: datetime | None
    batch_timeout_sec: int | None


@dataclass(frozen=True)
class KernelGroupResourceSlotData(FieldData):
    id: KernelGroupResourceSlotID
    kernel_group_id: KernelGroupID
    slot_name: ResourceSlotName
    quantity: Decimal


@dataclass(frozen=True)
class KernelGroupEnvironData(FieldData):
    kernel_group_id: KernelGroupID
    key: str
    value: str
