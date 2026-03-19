"""Domain Usage Bucket GQL types."""

from __future__ import annotations

from typing import Any, Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_usage.request import (
    DomainUsageBucketFilter as DomainUsageBucketFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    DomainUsageBucketOrderBy as DomainUsageBucketOrderByDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    DomainUsageBucketNode,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    UsageBucketMetadataNode as UsageBucketMetadataNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.types import (
    UsageBucketOrderField as UsageBucketOrderFieldDTO,
)
from ai.backend.manager.api.gql.base import (
    DateFilter,
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
)
from ai.backend.manager.api.gql.fair_share.types import ResourceSlotGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.repositories.resource_usage_history.options import (
    ProjectUsageBucketConditions,
)
from ai.backend.manager.repositories.resource_usage_history.types import (
    DomainUsageBucketData,
)

from .common import UsageBucketMetadataGQL, UsageBucketOrderField
from .common_calculations import (
    calculate_average_daily_usage,
    calculate_usage_capacity_ratio,
)
from .project_usage import (
    ProjectUsageBucketConnection,
    ProjectUsageBucketEdge,
    ProjectUsageBucketFilter,
    ProjectUsageBucketGQL,
    ProjectUsageBucketOrderBy,
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Domain-level usage bucket representing aggregated resource "
            "consumption for a specific time period. Usage buckets store historical data "
            "used to calculate fair share factors."
        ),
    ),
    name="DomainUsageBucket",
)
class DomainUsageBucketGQL(PydanticNodeMixin[DomainUsageBucketNode]):
    """Domain-level usage bucket containing aggregated resource usage for a period."""

    id: NodeID[str]
    domain_name: str = strawberry.field(
        description="Name of the domain this usage bucket belongs to."
    )
    resource_group_name: str = strawberry.field(
        description="Name of the scaling group this usage was recorded in."
    )
    metadata: UsageBucketMetadataGQL = strawberry.field(
        description="Metadata about the usage measurement period and timestamps."
    )
    resource_usage: ResourceSlotGQL = strawberry.field(
        description=(
            "Aggregated resource usage during this period. "
            "Contains the total compute resources consumed by all workloads in this domain "
            "during the measurement period (cpu cores, memory bytes, accelerator usage)."
        )
    )
    capacity_snapshot: ResourceSlotGQL = strawberry.field(
        description=(
            "Snapshot of total available capacity in the scaling group at the end of this period. "
            "Used as a reference to calculate relative usage and fair share factors."
        )
    )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.2.0. Average daily resource usage during this period. "
            "Calculated as resource_usage divided by bucket duration in days. "
            "For each resource type, this represents the average amount consumed per day. "
            "Units match the resource type (e.g., CPU cores, memory bytes)."
        )
    )
    def average_daily_usage(self) -> ResourceSlotGQL:
        return calculate_average_daily_usage(
            self.resource_usage,
            self.metadata.period_start,
            self.metadata.period_end,
        )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.2.0. Usage ratio against total available capacity for each resource. "
            "Calculated as resource_usage divided by capacity_snapshot. "
            "Represents the fraction of total capacity consumed (resource-seconds / resource). "
            "The result is in seconds, where 86400 means full utilization for one day. "
            "Values can exceed this if usage exceeds capacity."
        )
    )
    def usage_capacity_ratio(self) -> ResourceSlotGQL:
        return calculate_usage_capacity_ratio(
            self.resource_usage,
            self.capacity_snapshot,
        )

    @classmethod
    def from_dataclass(cls, data: DomainUsageBucketData) -> DomainUsageBucketGQL:
        return cls(
            id=ID(str(data.id)),
            domain_name=data.domain_name,
            resource_group_name=data.resource_group,
            metadata=UsageBucketMetadataGQL.from_pydantic(
                UsageBucketMetadataNodeDTO(
                    period_start=data.period_start,
                    period_end=data.period_end,
                    decay_unit_days=data.decay_unit_days,
                    created_at=data.created_at,
                    updated_at=data.updated_at,
                )
            ),
            resource_usage=ResourceSlotGQL.from_resource_slot(data.resource_usage),
            capacity_snapshot=ResourceSlotGQL.from_resource_slot(data.capacity_snapshot),
        )

    @classmethod
    def from_pydantic(
        cls,
        dto: DomainUsageBucketNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        """Create DomainUsageBucketGQL from DomainUsageBucketNode DTO (adapter search results)."""
        return cls(
            id=ID(str(dto.id)),
            domain_name=dto.domain_name,
            resource_group_name=dto.resource_group,
            metadata=UsageBucketMetadataGQL.from_pydantic(
                UsageBucketMetadataNodeDTO(
                    period_start=dto.period_start,
                    period_end=dto.period_end,
                    decay_unit_days=dto.decay_unit_days,
                    created_at=dto.created_at,
                    updated_at=dto.updated_at,
                )
            ),
            resource_usage=ResourceSlotGQL.from_resource_slot(dto.resource_usage),
            capacity_snapshot=ResourceSlotGQL.from_resource_slot(dto.capacity_snapshot),
        )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.1.0. Project usage buckets belonging to this domain. "
            "Returns paginated project-level usage history for all projects in this domain "
            "within the same scaling group."
        )
    )
    async def project_usage_buckets(
        self,
        info: Info[StrawberryGQLContext],
        filter: ProjectUsageBucketFilter | None = None,
        order_by: list[ProjectUsageBucketOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ProjectUsageBucketConnection:
        from strawberry.relay import PageInfo

        from ai.backend.manager.api.gql.base import encode_cursor

        payload = await info.context.adapters.resource_usage.gql_search_project_unscoped(
            base_conditions=[
                ProjectUsageBucketConditions.by_domain_name(self.domain_name),
                ProjectUsageBucketConditions.by_resource_group(self.resource_group_name),
                ProjectUsageBucketConditions.by_period_start(self.metadata.period_start),
            ],
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        nodes = [ProjectUsageBucketGQL.from_pydantic(item) for item in payload.items]
        edges = [
            ProjectUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
        ]
        return ProjectUsageBucketConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )


DomainUsageBucketEdge = Edge[DomainUsageBucketGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Paginated connection for domain usage bucket records. "
            "Provides relay-style cursor-based pagination for browsing historical usage data by time period. "
            "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
        ),
    ),
)
class DomainUsageBucketConnection(Connection[DomainUsageBucketGQL]):
    count: int = strawberry.field(
        description="Total number of domain usage bucket records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.experimental.pydantic.input(
    model=DomainUsageBucketFilterDTO,
    name="DomainUsageBucketFilter",
    description=(
        "Added in 26.1.0. Filter input for querying domain usage bucket records. "
        "Usage buckets contain historical resource consumption data aggregated by time period. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class DomainUsageBucketFilter(GQLFilter):
    """Filter for domain usage buckets."""

    resource_group: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by scaling group name. Scaling groups define where usage was recorded. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by domain name. This filters usage buckets for a specific domain. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    period_start: DateFilter | None = strawberry.field(
        default=None, description="Filter by usage measurement period start date."
    )
    period_end: DateFilter | None = strawberry.field(
        default=None, description="Filter by usage measurement period end date."
    )

    AND: list[DomainUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[DomainUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[DomainUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    def to_pydantic(self) -> DomainUsageBucketFilterDTO:
        return DomainUsageBucketFilterDTO(
            resource_group=self.resource_group.to_pydantic() if self.resource_group else None,
            domain_name=self.domain_name.to_pydantic() if self.domain_name else None,
            period_start=self.period_start.to_pydantic() if self.period_start else None,
            period_end=self.period_end.to_pydantic() if self.period_end else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=DomainUsageBucketOrderByDTO,
    name="DomainUsageBucketOrderBy",
    description=(
        "Added in 26.1.0. Specifies ordering for domain usage bucket query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (most recent first)."
    ),
)
class DomainUsageBucketOrderBy(GQLOrderBy):
    """OrderBy for domain usage buckets."""

    field: UsageBucketOrderField = strawberry.field(
        description="The field to order by. See UsageBucketOrderField for available options."
    )
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description=(
            "Sort direction. ASC for chronological order (oldest first), "
            "DESC for reverse chronological order (most recent first)."
        ),
    )

    def to_pydantic(self) -> DomainUsageBucketOrderByDTO:
        return DomainUsageBucketOrderByDTO(
            field=UsageBucketOrderFieldDTO(self.field.value),
            direction=OrderDirectionDTO(self.direction.value),
        )


__all__ = [
    "DomainUsageBucketGQL",
    "DomainUsageBucketConnection",
    "DomainUsageBucketEdge",
    "DomainUsageBucketFilter",
    "DomainUsageBucketOrderBy",
]
