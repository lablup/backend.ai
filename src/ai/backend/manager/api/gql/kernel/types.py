"""GraphQL types for kernel management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.base import (
    JSONString,
    OrderDirection,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders

KernelStatusGQL = strawberry.enum(KernelStatus, name="KernelStatus", description="Added in 26.1.0")


@strawberry.enum(description="Added in 26.1.0. Fields available for ordering kernels.")
class KernelOrderField(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(description="Added in 26.1.0. Filter for kernel status.")
class KernelStatusFilter:
    in_: list[KernelStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[KernelStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        if self.in_:
            return KernelConditions.by_statuses(self.in_)
        if self.not_in:
            # For not_in, we need all statuses except the ones in the list
            all_statuses = set(KernelStatus)
            allowed_statuses = all_statuses - set(self.not_in)
            return KernelConditions.by_statuses(list(allowed_statuses))
        return None


@strawberry.input(description="Added in 26.1.0. Filter criteria for querying kernels.")
class KernelFilter(GQLFilter):
    status: KernelStatusFilter | None = None
    session_id: UUID | None = None

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.status:
            condition = self.status.build_condition()
            if condition:
                conditions.append(condition)
        if self.session_id:
            conditions.append(KernelConditions.by_session_ids([SessionId(self.session_id)]))
        return conditions


@strawberry.input(description="Added in 26.1.0. Ordering specification for kernels.")
class KernelOrderBy(GQLOrderBy):
    field: KernelOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case KernelOrderField.CREATED_AT:
                return KernelOrders.created_at(ascending)
            case KernelOrderField.ID:
                return KernelOrders.id(ascending)


@strawberry.type(
    name="KernelV2",
    description="Added in 26.1.0. Represents a kernel (compute container) in Backend.AI.",
)
class KernelGQL(Node):
    """
    Kernel type representing a compute container.
    """

    id: NodeID[str]
    row_id: UUID
    cluster_idx: int
    local_rank: int
    cluster_role: str
    cluster_hostname: str
    session_id: UUID

    # Image info
    image_reference: str
    architecture: str

    # Status
    status: KernelStatusGQL
    status_changed: datetime | None
    status_info: str | None
    status_data: JSON | None
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
    scheduled_at: datetime | None

    # Resources
    agent_id: str | None
    agent_addr: str | None
    container_id: str | None
    resource_opts: JSON | None
    occupied_slots: JSONString
    preopen_ports: list[int] | None

    @classmethod
    def from_kernel_info(cls, kernel_info: KernelInfo, hide_agents: bool = False) -> Self:
        """Create KernelGQL from KernelInfo dataclass."""
        status_history = kernel_info.lifecycle.status_history or {}

        # Extract image reference from ImageInfo
        image_ref = ""
        architecture = ""
        if kernel_info.image.identifier:
            image_ref = kernel_info.image.identifier.canonical
            architecture = kernel_info.image.identifier.architecture
        elif kernel_info.image.architecture:
            architecture = kernel_info.image.architecture

        return cls(
            id=ID(str(kernel_info.id)),
            row_id=kernel_info.id,
            cluster_idx=kernel_info.cluster.cluster_idx,
            local_rank=kernel_info.cluster.local_rank,
            cluster_role=kernel_info.cluster.cluster_role,
            cluster_hostname=kernel_info.cluster.cluster_hostname,
            session_id=UUID(kernel_info.session.session_id),
            image_reference=image_ref,
            architecture=architecture,
            status=KernelStatusGQL(kernel_info.lifecycle.status),
            status_changed=kernel_info.lifecycle.status_changed,
            status_info=kernel_info.lifecycle.status_info,
            status_data=kernel_info.lifecycle.status_data,
            created_at=kernel_info.lifecycle.created_at,
            terminated_at=kernel_info.lifecycle.terminated_at,
            starts_at=kernel_info.lifecycle.starts_at,
            scheduled_at=status_history.get(KernelStatus.SCHEDULED.name),
            agent_id=kernel_info.resource.agent if not hide_agents else None,
            agent_addr=kernel_info.resource.agent_addr if not hide_agents else None,
            container_id=kernel_info.resource.container_id if not hide_agents else None,
            resource_opts=kernel_info.resource.resource_opts,
            occupied_slots=JSONString.from_resource_slot(kernel_info.resource.occupied_slots),
            preopen_ports=kernel_info.network.preopen_ports,
        )


KernelEdge = Edge[KernelGQL]


@strawberry.type(description="Added in 26.1.0. Connection type for paginated kernel results.")
class KernelConnectionV2(Connection[KernelGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
