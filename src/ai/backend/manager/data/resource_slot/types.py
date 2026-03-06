from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.types import SlotQuantity


@dataclass(frozen=True)
class NumberFormatData:
    binary: bool = False
    round_length: int = 0


@dataclass(frozen=True)
class ResourceSlotTypeData:
    slot_name: str
    slot_type: str
    display_name: str
    description: str
    display_unit: str
    display_icon: str
    number_format: NumberFormatData
    rank: int


@dataclass(frozen=True)
class ResourceSlotTypeSearchResult:
    items: list[ResourceSlotTypeData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class AgentResourceData:
    agent_id: str
    slot_name: str
    capacity: Decimal
    used: Decimal


@dataclass(frozen=True)
class AgentResourceSearchResult:
    items: list[AgentResourceData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ResourceAllocationData:
    kernel_id: uuid.UUID
    slot_name: str
    requested: Decimal
    used: Decimal | None


@dataclass(frozen=True)
class ResourceAllocationSearchResult:
    items: list[ResourceAllocationData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ResourceOccupancy:
    used_slots: list[SlotQuantity]
    session_count: int
