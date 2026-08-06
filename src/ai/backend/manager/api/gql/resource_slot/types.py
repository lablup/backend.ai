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
from typing import Any, Self, override

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AgentResourceFilter as AgentResourceFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AgentResourceOrder as AgentResourceOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    CreateResourceSlotTypeInput as CreateResourceSlotTypeInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    PurgeResourceSlotTypeInput as PurgeResourceSlotTypeInputDTO,
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
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    UpdateResourceSlotTypeInput as UpdateResourceSlotTypeInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AgentResourceNode as AgentResourceNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    CreateResourceSlotTypePayload as CreateResourceSlotTypePayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    PurgeResourceSlotTypePayload as PurgeResourceSlotTypePayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ResourceAllocationNode as ResourceAllocationNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ResourceSlotTypeNode as ResourceSlotTypeNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    UpdateResourceSlotTypePayload as UpdateResourceSlotTypePayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    NumberFormatInfo as NumberFormatInfoDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    NumberFormatInput as NumberFormatInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
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
    binary: bool = gql_field(
        description="Whether to use binary (1024-based) or decimal (1000-based) prefixes."
    )
    round_length: int = gql_field(
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
    slot_name: str = gql_field(
        description="Unique identifier for the resource slot (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    slot_type: str = gql_field(
        description="Category of the slot type: one of 'count', 'bytes', 'unique', 'unified'."
    )
    required: bool = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Whether a session request must name this slot.",
        ),
    )
    enabled: bool = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Whether the scheduler considers this slot when placing sessions. "
                "A disabled slot is ignored by the image slot-type rule."
            ),
        ),
    )
    display_name: str = gql_field(description="Human-readable name for display in UIs.")
    description: str = gql_field(
        description="Longer description of what this resource slot represents."
    )
    display_unit: str = gql_field(
        description="Unit label used when displaying resource amounts (e.g., 'GiB', 'cores')."
    )
    display_icon: str = gql_field(
        description="Icon identifier for UI rendering (e.g., 'cpu', 'memory', 'gpu')."
    )
    number_format: NumberFormatGQL = gql_field(
        description="Number formatting rules (binary vs decimal prefix, rounding)."
    )
    rank: int = gql_field(description="Display ordering rank. Lower values appear first.")

    @classmethod
    @override
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


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering resource slot types.",
    ),
    name="ResourceSlotTypeOrderField",
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


# ========== ResourceSlotType mutation inputs / payloads ==========


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Number format configuration written with a resource slot type.",
    ),
    name="NumberFormatInput",
)
class NumberFormatInputGQL(PydanticInputMixin[NumberFormatInputDTO]):
    binary: bool = gql_field(
        description="Whether to use binary (1024-based) or decimal (1000-based) prefixes.",
        default=False,
    )
    round_length: int = gql_field(
        description="Number of decimal places to round to when displaying values.", default=0
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for registering a new resource slot type.",
    ),
    name="CreateResourceSlotTypeInput",
)
class CreateResourceSlotTypeInputGQL(PydanticInputMixin[CreateResourceSlotTypeInputDTO]):
    slot_name: str = gql_field(description="Unique slot name to register.")
    slot_type: str = gql_field(
        description="Category of the slot type: one of 'count', 'bytes', 'unique', 'unified'."
    )
    required: bool = gql_field(
        description="Whether a session request must name this slot.", default=False
    )
    enabled: bool = gql_field(
        description="Whether the scheduler considers this slot when placing sessions.",
        default=True,
    )
    display_name: str = gql_field(description="Human-readable name.", default="")
    description: str = gql_field(description="Longer description.", default="")
    display_unit: str = gql_field(description="Unit label (e.g., 'GiB').", default="")
    display_icon: str = gql_field(description="Icon identifier for UIs.", default="")
    number_format: NumberFormatInputGQL | None = gql_field(
        description="Number formatting rules. Defaults to decimal with no rounding.", default=None
    )
    rank: int = gql_field(
        description="Display ordering rank. Lower values appear first.", default=0
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for resource slot type registration.",
    ),
    model=CreateResourceSlotTypePayloadDTO,
    name="CreateResourceSlotTypePayload",
)
class CreateResourceSlotTypePayloadGQL:
    resource_slot_type: ResourceSlotTypeGQL = gql_field(
        description="The registered resource slot type."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for updating a resource slot type. The slot name and slot type are "
            "immutable; omitted fields stay unchanged."
        ),
    ),
    name="UpdateResourceSlotTypeInput",
)
class UpdateResourceSlotTypeInputGQL(PydanticInputMixin[UpdateResourceSlotTypeInputDTO]):
    slot_name: str = gql_field(description="Slot name identifying the slot type to update.")
    required: bool | None = gql_field(
        description="Whether a session request must name this slot.", default=None
    )
    enabled: bool | None = gql_field(
        description="Whether the scheduler considers this slot when placing sessions.",
        default=None,
    )
    display_name: str | None = gql_field(description="Human-readable name.", default=None)
    description: str | None = gql_field(description="Longer description.", default=None)
    display_unit: str | None = gql_field(description="Unit label (e.g., 'GiB').", default=None)
    display_icon: str | None = gql_field(description="Icon identifier for UIs.", default=None)
    number_format: NumberFormatInputGQL | None = gql_field(
        description="Number formatting rules.", default=None
    )
    rank: int | None = gql_field(description="Display ordering rank.", default=None)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for resource slot type update.",
    ),
    model=UpdateResourceSlotTypePayloadDTO,
    name="UpdateResourceSlotTypePayload",
)
class UpdateResourceSlotTypePayloadGQL:
    resource_slot_type: ResourceSlotTypeGQL = gql_field(
        description="The updated resource slot type."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for removing a resource slot type.",
    ),
    name="PurgeResourceSlotTypeInput",
)
class PurgeResourceSlotTypeInputGQL(PydanticInputMixin[PurgeResourceSlotTypeInputDTO]):
    slot_name: str = gql_field(description="Slot name identifying the slot type to remove.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for resource slot type removal.",
    ),
    model=PurgeResourceSlotTypePayloadDTO,
    name="PurgeResourceSlotTypePayload",
)
class PurgeResourceSlotTypePayloadGQL:
    slot_name: str = gql_field(description="Slot name of the removed resource slot type.")


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
    slot_name: str = gql_field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    capacity: Decimal = gql_field(
        description="Total hardware resource capacity for this slot on the agent."
    )
    used: Decimal = gql_field(
        description="Amount of this slot currently consumed by running and scheduled sessions."
    )

    @classmethod
    @override
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


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering agent resource slots.",
    ),
    name="AgentResourceSlotOrderField",
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
    slot_name: str = gql_field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    requested: Decimal = gql_field(
        description="Amount of this resource slot originally requested for the kernel."
    )
    used: Decimal | None = gql_field(
        description="Amount currently used. May be null if not yet measured."
    )

    @classmethod
    @override
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


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering kernel resource allocations.",
    ),
    name="KernelResourceAllocationOrderField",
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
