"""GraphQL types for resource slot management.

Covers:
- ResourceSlotTypeGQL: Registry node for a known resource slot type (resource_slot_types table)
- AgentResourceSlotGQL: Per-slot capacity/usage on an agent (agent_resources table)
- KernelResourceAllocationGQL: Per-slot allocation for a kernel (resource_allocations table)
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any, Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    NumberFormatData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)

# ========== NumberFormat ==========


@strawberry.type(
    name="NumberFormat",
    description="Added in 26.4.0. Display number format configuration for a resource slot type.",
)
class NumberFormatGQL:
    binary: bool = strawberry.field(
        description="Whether to use binary (1024-based) prefix instead of decimal (1000-based)."
    )
    round_length: int = strawberry.field(description="Number of decimal places to display.")

    @classmethod
    def from_data(cls, data: NumberFormatData) -> Self:
        return cls(binary=data.binary, round_length=data.round_length)


# ========== ResourceSlotTypeGQL (Node) ==========


@strawberry.type(
    name="ResourceSlotType",
    description=dedent_strip("""
        Added in 26.4.0. A registered resource slot type describing display metadata
        and formatting rules for a specific resource (e.g., cpu, mem, cuda.device).
    """),
)
class ResourceSlotTypeGQL(Node):
    id: NodeID[str]
    slot_name: str = strawberry.field(
        description="Unique identifier for the resource slot (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    slot_type: str = strawberry.field(
        description="Category of the slot type (e.g., 'count', 'bytes', 'unique-count')."
    )
    display_name: str = strawberry.field(description="Human-readable name for display in UIs.")
    description: str = strawberry.field(
        description="Longer description of what this resource slot represents."
    )
    display_unit: str = strawberry.field(
        description="Unit label used when displaying resource amounts (e.g., 'GiB', 'cores')."
    )
    display_icon: str = strawberry.field(
        description="Icon identifier for UI rendering (e.g., 'cpu', 'memory', 'gpu')."
    )
    number_format: NumberFormatGQL = strawberry.field(
        description="Number formatting rules (binary vs decimal prefix, rounding)."
    )
    rank: int = strawberry.field(description="Display ordering rank. Lower values appear first.")

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        from ai.backend.manager.api.gql.resource_slot.fetcher import fetch_resource_slot_type

        results = []
        for slot_name in node_ids:
            node = await fetch_resource_slot_type(info, slot_name)
            results.append(node)
        return results

    @classmethod
    def from_data(cls, data: ResourceSlotTypeData) -> Self:
        return cls(
            id=ID(data.slot_name),
            slot_name=data.slot_name,
            slot_type=data.slot_type,
            display_name=data.display_name,
            description=data.description,
            display_unit=data.display_unit,
            display_icon=data.display_icon,
            number_format=NumberFormatGQL.from_data(data.number_format),
            rank=data.rank,
        )


ResourceSlotTypeEdgeGQL = Edge[ResourceSlotTypeGQL]


@strawberry.type(
    name="ResourceSlotTypeConnection",
    description="Added in 26.4.0. Relay-style connection for paginated resource slot types.",
)
class ResourceSlotTypeConnectionGQL(Connection[ResourceSlotTypeGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ========== AgentResourceSlotGQL (Node) ==========


@strawberry.type(
    name="AgentResourceSlot",
    description=dedent_strip("""
        Added in 26.4.0. Per-slot resource capacity and usage entry for an agent.
        Represents one row from the agent_resources table.
    """),
)
class AgentResourceSlotGQL(Node):
    """Per-agent, per-slot resource capacity and usage."""

    id: NodeID[str]
    slot_name: str = strawberry.field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    capacity: Decimal = strawberry.field(
        description="Total hardware resource capacity for this slot on the agent."
    )
    used: Decimal = strawberry.field(
        description="Amount of this slot currently consumed by running and scheduled sessions."
    )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # Node ID format: "{agent_id}:{slot_name}"
        results = []
        for node_id in node_ids:
            agent_id, _, slot_name = node_id.partition(":")
            from ai.backend.manager.api.gql.resource_slot.fetcher import (
                fetch_agent_resource_slot,
            )

            node = await fetch_agent_resource_slot(info, agent_id, slot_name)
            results.append(node)
        return results

    @classmethod
    def from_data(cls, data: AgentResourceData) -> Self:
        node_id = f"{data.agent_id}:{data.slot_name}"
        return cls(
            id=ID(node_id),
            slot_name=data.slot_name,
            capacity=data.capacity,
            used=data.used,
        )


AgentResourceSlotEdgeGQL = Edge[AgentResourceSlotGQL]


@strawberry.type(
    name="AgentResourceConnection",
    description="Added in 26.4.0. Relay-style connection for per-slot agent resources.",
)
class AgentResourceConnectionGQL(Connection[AgentResourceSlotGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ========== KernelResourceAllocationGQL (Node) ==========


@strawberry.type(
    name="KernelResourceAllocation",
    description=dedent_strip("""
        Added in 26.4.0. Per-slot resource allocation entry for a kernel.
        Represents one row from the resource_allocations table.
    """),
)
class KernelResourceAllocationGQL(Node):
    """Per-kernel, per-slot resource allocation."""

    id: NodeID[str]
    slot_name: str = strawberry.field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    requested: Decimal = strawberry.field(
        description="Amount of this resource slot originally requested for the kernel."
    )
    used: Decimal | None = strawberry.field(
        description="Amount currently used. May be null if not yet measured."
    )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # Node ID format: "{kernel_id}:{slot_name}"
        results = []
        for node_id in node_ids:
            kernel_id_str, _, slot_name = node_id.partition(":")
            from ai.backend.manager.api.gql.resource_slot.fetcher import (
                fetch_kernel_resource_allocation,
            )

            node = await fetch_kernel_resource_allocation(info, kernel_id_str, slot_name)
            results.append(node)
        return results

    @classmethod
    def from_data(cls, data: ResourceAllocationData) -> Self:
        node_id = f"{data.kernel_id}:{data.slot_name}"
        return cls(
            id=ID(node_id),
            slot_name=data.slot_name,
            requested=data.requested,
            used=data.used,
        )


KernelResourceAllocationEdgeGQL = Edge[KernelResourceAllocationGQL]


@strawberry.type(
    name="ResourceAllocationConnection",
    description="Added in 26.4.0. Relay-style connection for per-slot kernel resource allocations.",
)
class ResourceAllocationConnectionGQL(Connection[KernelResourceAllocationGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
