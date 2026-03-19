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
from typing import Any, Self, cast

import strawberry
from strawberry import ID, Info
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
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    AgentResourceOrderField as AgentResourceOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    NumberFormatInfo as NumberFormatInfoDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    OrderDirection as DtoOrderDirection,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    ResourceAllocationOrderField as ResourceAllocationOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    ResourceSlotTypeOrderField as ResourceSlotTypeOrderFieldDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.services.resource_slot.actions.get_agent_resource_by_slot import (
    GetAgentResourceBySlotAction,
)
from ai.backend.manager.services.resource_slot.actions.get_kernel_allocation_by_slot import (
    GetKernelAllocationBySlotAction,
)
from ai.backend.manager.services.resource_slot.actions.get_resource_slot_type import (
    GetResourceSlotTypeAction,
)

# ========== Raw data helpers for Node.resolve_nodes ==========
# These return raw data types so that resolve_nodes can call cls.from_data(),
# which enables mypy to correctly infer the return type as Iterable[Self | None].


async def load_resource_slot_type_data(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeData:
    """Load raw ResourceSlotTypeData for a single slot_name (used by Node.resolve_nodes)."""
    action_result = (
        await info.context.processors.resource_slot.get_resource_slot_type.wait_for_complete(
            GetResourceSlotTypeAction(slot_name=slot_name)
        )
    )
    return cast(ResourceSlotTypeData, action_result.item)


async def load_agent_resource_data(
    info: Info[StrawberryGQLContext],
    agent_id: str,
    slot_name: str,
) -> AgentResourceData:
    """Load raw AgentResourceData for a single agent+slot (used by Node.resolve_nodes).

    Raises AgentResourceNotFound if the entry does not exist.
    """
    action_result = (
        await info.context.processors.resource_slot.get_agent_resource_by_slot.wait_for_complete(
            GetAgentResourceBySlotAction(agent_id=agent_id, slot_name=slot_name)
        )
    )
    return cast(AgentResourceData, action_result.item)


async def load_kernel_allocation_data(
    info: Info[StrawberryGQLContext],
    kernel_id_str: str,
    slot_name: str,
) -> ResourceAllocationData:
    """Load raw ResourceAllocationData for a single kernel+slot (used by Node.resolve_nodes).

    Raises ResourceAllocationNotFound if the entry does not exist.
    """
    action_result = (
        await info.context.processors.resource_slot.get_kernel_allocation_by_slot.wait_for_complete(
            GetKernelAllocationBySlotAction(
                kernel_id=_uuid.UUID(kernel_id_str), slot_name=slot_name
            )
        )
    )
    return cast(ResourceAllocationData, action_result.item)


# ========== NumberFormat ==========


@strawberry.experimental.pydantic.type(
    model=NumberFormatInfoDTO,
    name="NumberFormat",
    description="Added in 26.3.0. Display number format configuration for a resource slot type.",
    all_fields=True,
)
class NumberFormatGQL:
    pass


# ========== ResourceSlotTypeGQL (Node) ==========


@strawberry.type(
    name="ResourceSlotType",
    description=dedent_strip("""
        Added in 26.3.0. A registered resource slot type describing display metadata
        and formatting rules for a specific resource (e.g., cpu, mem, cuda.device).
    """),
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
                data = await load_resource_slot_type_data(info, slot_name)
            except ResourceSlotTypeNotFound:
                if required:
                    raise
                results.append(None)
            else:
                results.append(cls.from_data(data))
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
            number_format=NumberFormatGQL.from_pydantic(
                NumberFormatInfoDTO(
                    binary=data.number_format.binary,
                    round_length=data.number_format.round_length,
                )
            ),
            rank=data.rank,
        )


ResourceSlotTypeEdgeGQL = Edge[ResourceSlotTypeGQL]


@strawberry.type(
    name="ResourceSlotTypeConnection",
    description="Added in 26.3.0. Relay-style connection for paginated resource slot types.",
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


@strawberry.experimental.pydantic.input(
    model=ResourceSlotTypeFilterDTO,
    name="ResourceSlotTypeFilter",
    description="Added in 26.3.0. Filter criteria for querying resource slot types.",
)
class ResourceSlotTypeFilterGQL:
    slot_name: StringFilter | None = None
    slot_type: StringFilter | None = None
    display_name: StringFilter | None = None

    AND: list[ResourceSlotTypeFilterGQL] | None = None
    OR: list[ResourceSlotTypeFilterGQL] | None = None
    NOT: list[ResourceSlotTypeFilterGQL] | None = None

    def to_pydantic(self) -> ResourceSlotTypeFilterDTO:
        return ResourceSlotTypeFilterDTO(
            slot_name=self.slot_name.to_pydantic() if self.slot_name is not None else None,
            slot_type=self.slot_type.to_pydantic() if self.slot_type is not None else None,
            display_name=self.display_name.to_pydantic() if self.display_name is not None else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND is not None else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR is not None else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT is not None else None,
        )


@strawberry.experimental.pydantic.input(
    model=ResourceSlotTypeOrderDTO,
    name="ResourceSlotTypeOrderBy",
    description="Added in 26.3.0. Ordering specification for resource slot types.",
)
class ResourceSlotTypeOrderByGQL:
    field: ResourceSlotTypeOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ResourceSlotTypeOrderDTO:
        return ResourceSlotTypeOrderDTO(
            field=ResourceSlotTypeOrderFieldDTO(self.field.value),
            direction=DtoOrderDirection(self.direction.value),
        )


# ========== AgentResourceSlotGQL (Node) ==========


@strawberry.type(
    name="AgentResourceSlot",
    description=dedent_strip("""
        Added in 26.3.0. Per-slot resource capacity and usage entry for an agent.
        Represents one row from the agent_resources table.
    """),
)
class AgentResourceSlotGQL(PydanticNodeMixin[Any]):
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
                data = await load_agent_resource_data(info, agent_id, slot_name)
            except AgentResourceNotFound:
                if required:
                    raise
                results.append(None)
            else:
                results.append(cls.from_data(data))
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
    description="Added in 26.3.0. Relay-style connection for per-slot agent resources.",
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


@strawberry.experimental.pydantic.input(
    model=AgentResourceFilterDTO,
    name="AgentResourceSlotFilter",
    description="Added in 26.3.0. Filter criteria for querying agent resource slots.",
)
class AgentResourceSlotFilterGQL:
    slot_name: StringFilter | None = None
    agent_id: StringFilter | None = None

    AND: list[AgentResourceSlotFilterGQL] | None = None
    OR: list[AgentResourceSlotFilterGQL] | None = None
    NOT: list[AgentResourceSlotFilterGQL] | None = None

    def to_pydantic(self) -> AgentResourceFilterDTO:
        return AgentResourceFilterDTO(
            slot_name=self.slot_name.to_pydantic() if self.slot_name is not None else None,
            agent_id=self.agent_id.to_pydantic() if self.agent_id is not None else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND is not None else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR is not None else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT is not None else None,
        )


@strawberry.experimental.pydantic.input(
    model=AgentResourceOrderDTO,
    name="AgentResourceSlotOrderBy",
    description="Added in 26.3.0. Ordering specification for agent resource slots.",
)
class AgentResourceSlotOrderByGQL:
    field: AgentResourceSlotOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> AgentResourceOrderDTO:
        return AgentResourceOrderDTO(
            field=AgentResourceOrderFieldDTO(self.field.value),
            direction=DtoOrderDirection(self.direction.value),
        )


# ========== KernelResourceAllocationGQL (Node) ==========


@strawberry.type(
    name="KernelResourceAllocation",
    description=dedent_strip("""
        Added in 26.3.0. Per-slot resource allocation entry for a kernel.
        Represents one row from the resource_allocations table.
    """),
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
                data = await load_kernel_allocation_data(info, kernel_id_str, slot_name)
            except ResourceAllocationNotFound:
                if required:
                    raise
                results.append(None)
            else:
                results.append(cls.from_data(data))
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


# ========== KernelResourceAllocation Filter/OrderBy ==========


@strawberry.enum(
    name="KernelResourceAllocationOrderField",
    description="Added in 26.3.0. Fields available for ordering kernel resource allocations.",
)
class KernelResourceAllocationOrderFieldGQL(StrEnum):
    SLOT_NAME = "slot_name"
    REQUESTED = "requested"
    USED = "used"


@strawberry.experimental.pydantic.input(
    model=ResourceAllocationFilterDTO,
    name="KernelResourceAllocationFilter",
    description="Added in 26.3.0. Filter criteria for querying kernel resource allocations.",
)
class KernelResourceAllocationFilterGQL:
    slot_name: StringFilter | None = None

    AND: list[KernelResourceAllocationFilterGQL] | None = None
    OR: list[KernelResourceAllocationFilterGQL] | None = None
    NOT: list[KernelResourceAllocationFilterGQL] | None = None

    def to_pydantic(self) -> ResourceAllocationFilterDTO:
        return ResourceAllocationFilterDTO(
            slot_name=self.slot_name.to_pydantic() if self.slot_name is not None else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND is not None else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR is not None else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT is not None else None,
        )


@strawberry.experimental.pydantic.input(
    model=ResourceAllocationOrderDTO,
    name="KernelResourceAllocationOrderBy",
    description="Added in 26.3.0. Ordering specification for kernel resource allocations.",
)
class KernelResourceAllocationOrderByGQL:
    field: KernelResourceAllocationOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ResourceAllocationOrderDTO:
        return ResourceAllocationOrderDTO(
            field=ResourceAllocationOrderFieldDTO(self.field.value),
            direction=DtoOrderDirection(self.direction.value),
        )


KernelResourceAllocationEdgeGQL = Edge[KernelResourceAllocationGQL]


@strawberry.type(
    name="ResourceAllocationConnection",
    description="Added in 26.3.0. Relay-style connection for per-slot kernel resource allocations.",
)
class ResourceAllocationConnectionGQL(Connection[KernelResourceAllocationGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
