from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.types import ResourceSlot, SlotQuantity


@dataclass(frozen=True)
class ResourceAllocationAggregate:
    """Per-owner (session or kernel) resource allocation aggregated from the
    ``resource_allocations`` table.

    - ``requested``: SUM(requested) over the owner's slots.
    - ``used``: currently occupying resources (``free_at IS NULL``); empties after free.
    - ``allocated``: resources ever actually allocated (``used_at IS NOT NULL``);
      persists after the owner is freed/terminated (for statistics/billing).
    """

    requested: ResourceSlot
    used: ResourceSlot
    allocated: ResourceSlot


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
    reserved: Decimal
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


@dataclass(frozen=True)
class AgentResourceDrift:
    agent_id: str
    slot_name: str
    tracked: Decimal
    actual: Decimal


@dataclass(frozen=True)
class OrphanedAllocation:
    kernel_id: uuid.UUID
    slot_name: str


@dataclass(frozen=True)
class TerminalSessionKernelReconciliation:
    """A non-terminal kernel whose session is already terminal, force-closed to
    CANCELLED by reconciliation. Carried out in bulk regardless of the session's
    specific terminal sub-state — this is abnormal-state cleanup, not a faithful
    replay of a state transition.
    """

    kernel_id: uuid.UUID
    session_id: uuid.UUID
    from_kernel_status: str


@dataclass(frozen=True)
class ReconciliationResult:
    reconciled_terminal_kernels: list[TerminalSessionKernelReconciliation]
    orphaned_allocations: list[OrphanedAllocation]
    agent_resource_drifts: list[AgentResourceDrift]
