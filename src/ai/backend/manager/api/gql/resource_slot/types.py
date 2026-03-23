"""GraphQL types for resource slot management.

Covers:
- ResourceSlotTypeGQL: Registry node for a known resource slot type (resource_slot_types table)
- AgentResourceSlotGQL: Per-slot capacity/usage on an agent (agent_resources table)
- KernelResourceAllocationGQL: Per-slot allocation for a kernel (resource_allocations table)
"""

from __future__ import annotations

import uuid as _uuid
from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AgentResourceFilter as AgentResourceFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AgentResourceOrder as AgentResourceOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    ResourceAllocationFilter as ResourceAllocationFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    ResourceAllocationOrder as ResourceAllocationOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    ResourceSlotTypeFilter as ResourceSlotTypeFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    ResourceSlotTypeOrder as ResourceSlotTypeOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AgentResourceNode as AgentResourceNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ResourceAllocationNode as ResourceAllocationNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ResourceSlotTypeNode as ResourceSlotTypeNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    NumberFormatInfo as NumberFormatInfoDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip

# ========== DTO helpers for Node.resolve_nodes ==========


async def load_resource_slot_type_node(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeNodeDTO:
    """Load a ResourceSlotTypeNode DTO for a single slot_name (used by Node.resolve_nodes)."""
    return await info.context.adapters.resource_slot.get_slot_type(slot_name)


async def load_agent_resource_node(
    info: Info[StrawberryGQLContext],
    agent_id: str,
    slot_name: str,
) -> AgentResourceNodeDTO:
    """Load an AgentResourceNode DTO for a single agent+slot (used by Node.resolve_nodes).

    Raises AgentResourceNotFound if the entry does not exist.
    """
    return await info.context.adapters.resource_slot.get_agent_resource(agent_id, slot_name)


async def load_kernel_allocation_node(
    info: Info[StrawberryGQLContext],
    kernel_id_str: str,
    slot_name: str,
) -> ResourceAllocationNodeDTO:
    """Load a ResourceAllocationNode DTO for a single kernel+slot (used by Node.resolve_nodes).

    Raises ResourceAllocationNotFound if the entry does not exist.
    """
    return await info.context.adapters.resource_slot.get_kernel_allocation(
        _uuid.UUID(kernel_id_str), slot_name
    )


# ========== NumberFormat ==========


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Display number format configuration for a resource slot type.",
    ),
    model=NumberFormatInfoDTO,
    name="NumberFormat",
)
class NumberFormatGQL:
    binary: bool = strawberry.field(
        description="Whether to use binary (1024-based) or decimal (1000-based) prefixes."
    )
    round_length: int = strawberry.field(
        description="Number of decimal places to round to when displaying values."
    )


# ========== ResourceSlotTypeGQL (Node) ==========


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description=dedent_strip("""
            A registered resource slot type describing display metadata
            and formatting rules for a specific resource (e.g., cpu, mem, cuda.device).
        """),
    ),
    name="ResourceSlotType",
)
class ResourceSlotTypeGQL(PydanticNodeMixin[Any]):
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
        from ai.backend.manager.errors.resource_slot import ResourceSlotTypeNotFound

        results: list[Self | None] = []
        for slot_name in node_ids:
            try:
                node = await load_resource_slot_type_node(info, slot_name)
            except ResourceSlotTypeNotFound:
                if required:
                    raise
                results.append(None)
            else:
                results.append(cls.from_pydantic(node))
        return results


ResourceSlotTypeEdgeGQL = Edge[ResourceSlotTypeGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Relay-style connection for paginated resource slot types.",
    ),
    name="ResourceSlotTypeConnection",
)
class ResourceSlotTypeConnectionGQL(Connection[ResourceSlotTypeGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ========== ResourceSlotType Filter/OrderBy ==========


@strawberry.enum(
    name="ResourceSlotTypeOrderField",
    description="Added in 26.3.0. Fields available for ordering resource slot types.",
)
class ResourceSlotTypeOrderFieldGQL(StrEnum):
    SLOT_NAME = "slot_name"
    RANK = "rank"
    DISPLAY_NAME = "display_name"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying resource slot types.", added_version="26.3.0"
    ),
    name="ResourceSlotTypeFilter",
)
class ResourceSlotTypeFilterGQL(PydanticInputMixin[ResourceSlotTypeFilterDTO]):
    slot_name: StringFilter | None = None
    slot_type: StringFilter | None = None
    display_name: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Ordering specification for resource slot types.", added_version="26.3.0"
    ),
    name="ResourceSlotTypeOrderBy",
)
class ResourceSlotTypeOrderByGQL(PydanticInputMixin[ResourceSlotTypeOrderDTO]):
    field: ResourceSlotTypeOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


# ========== AgentResourceSlotGQL (Node) ==========


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description=dedent_strip("""
            Per-slot resource capacity and usage entry for an agent.
            Represents one row from the agent_resources table.
        """),
    ),
    name="AgentResourceSlot",
)
class AgentResourceSlotGQL(PydanticNodeMixin[AgentResourceNodeDTO]):
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
        from ai.backend.manager.errors.resource_slot import AgentResourceNotFound

        results: list[Self | None] = []
        for node_id in node_ids:
            agent_id, _, slot_name = node_id.partition(":")
            try:
                node = await load_agent_resource_node(info, agent_id, slot_name)
            except AgentResourceNotFound:
                if required:
                    raise
                results.append(None)
            else:
                results.append(cls.from_pydantic(node))
        return results


AgentResourceSlotEdgeGQL = Edge[AgentResourceSlotGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Relay-style connection for per-slot agent resources.",
    ),
    name="AgentResourceConnection",
)
class AgentResourceConnectionGQL(Connection[AgentResourceSlotGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ========== AgentResourceSlot Filter/OrderBy ==========


@strawberry.enum(
    name="AgentResourceSlotOrderField",
    description="Added in 26.3.0. Fields available for ordering agent resource slots.",
)
class AgentResourceSlotOrderFieldGQL(StrEnum):
    SLOT_NAME = "slot_name"
    CAPACITY = "capacity"
    USED = "used"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying agent resource slots.", added_version="26.3.0"
    ),
    name="AgentResourceSlotFilter",
)
class AgentResourceSlotFilterGQL(PydanticInputMixin[AgentResourceFilterDTO]):
    slot_name: StringFilter | None = None
    agent_id: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Ordering specification for agent resource slots.", added_version="26.3.0"
    ),
    name="AgentResourceSlotOrderBy",
)
class AgentResourceSlotOrderByGQL(PydanticInputMixin[AgentResourceOrderDTO]):
    field: AgentResourceSlotOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


# ========== KernelResourceAllocationGQL (Node) ==========


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description=dedent_strip("""
            Per-slot resource allocation entry for a kernel.
            Represents one row from the resource_allocations table.
        """),
    ),
    name="KernelResourceAllocation",
)
class KernelResourceAllocationGQL(PydanticNodeMixin[Any]):
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
        from ai.backend.manager.errors.resource_slot import ResourceAllocationNotFound

        results: list[Self | None] = []
        for node_id in node_ids:
            kernel_id_str, _, slot_name = node_id.partition(":")
            try:
                node = await load_kernel_allocation_node(info, kernel_id_str, slot_name)
            except ResourceAllocationNotFound:
                if required:
                    raise
                results.append(None)
            else:
                results.append(cls.from_pydantic(node))
        return results


# ========== KernelResourceAllocation Filter/OrderBy ==========


@strawberry.enum(
    name="KernelResourceAllocationOrderField",
    description="Added in 26.3.0. Fields available for ordering kernel resource allocations.",
)
class KernelResourceAllocationOrderFieldGQL(StrEnum):
    SLOT_NAME = "slot_name"
    REQUESTED = "requested"
    USED = "used"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying kernel resource allocations.",
        added_version="26.3.0",
    ),
    name="KernelResourceAllocationFilter",
)
class KernelResourceAllocationFilterGQL(PydanticInputMixin[ResourceAllocationFilterDTO]):
    slot_name: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Ordering specification for kernel resource allocations.",
        added_version="26.3.0",
    ),
    name="KernelResourceAllocationOrderBy",
)
class KernelResourceAllocationOrderByGQL(PydanticInputMixin[ResourceAllocationOrderDTO]):
    field: KernelResourceAllocationOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


KernelResourceAllocationEdgeGQL = Edge[KernelResourceAllocationGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Relay-style connection for per-slot kernel resource allocations.",
    ),
    name="ResourceAllocationConnection",
)
class ResourceAllocationConnectionGQL(Connection[KernelResourceAllocationGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
