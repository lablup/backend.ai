"""User Usage Bucket GQL types."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_usage.request import (
    UserUsageBucketFilter as UserUsageBucketFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    UserUsageBucketOrderBy as UserUsageBucketOrderByDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    UsageBucketMetadataNode as UsageBucketMetadataNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    UserUsageBucketNode,
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
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.fair_share.types import ResourceSlotGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.repositories.resource_usage_history.types import (
    UserUsageBucketData,
)

from .common import UsageBucketMetadataGQL, UsageBucketOrderField
from .common_calculations import (
    calculate_average_daily_usage,
    calculate_usage_capacity_ratio,
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "User-level usage bucket representing aggregated resource "
            "consumption for a specific time period. This is the most granular level of usage tracking."
        ),
    ),
    name="UserUsageBucket",
)
class UserUsageBucketGQL(PydanticNodeMixin[UserUsageBucketNode]):
    """User-level usage bucket containing aggregated resource usage for a period."""

    id: NodeID[str]
    user_uuid: UUID = strawberry.field(description="UUID of the user this usage bucket belongs to.")
    project_id: UUID = strawberry.field(description="UUID of the project the user belongs to.")
    domain_name: str = strawberry.field(description="Name of the domain the user belongs to.")
    resource_group_name: str = strawberry.field(
        description="Name of the scaling group this usage was recorded in."
    )
    metadata: UsageBucketMetadataGQL = strawberry.field(
        description="Metadata about the usage measurement period and timestamps."
    )
    resource_usage: ResourceSlotGQL = strawberry.field(
        description=(
            "Aggregated resource usage during this period. "
            "Contains the total compute resources consumed by this user's workloads "
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
    def from_dataclass(cls, data: UserUsageBucketData) -> UserUsageBucketGQL:
        return cls(
            id=ID(str(data.id)),
            user_uuid=data.user_uuid,
            project_id=data.project_id,
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
        dto: UserUsageBucketNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        """Create UserUsageBucketGQL from UserUsageBucketNode DTO (adapter search results)."""
        return cls(
            id=ID(str(dto.id)),
            user_uuid=dto.user_uuid,
            project_id=dto.project_id,
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


UserUsageBucketEdge = Edge[UserUsageBucketGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Paginated connection for user usage bucket records. "
            "Provides relay-style cursor-based pagination for browsing historical usage data by time period. "
            "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
        ),
    ),
)
class UserUsageBucketConnection(Connection[UserUsageBucketGQL]):
    count: int = strawberry.field(
        description="Total number of user usage bucket records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying user usage bucket records. Usage buckets contain historical resource consumption data aggregated by time period for users. This is the most granular level of usage bucket filtering. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.1.0",
    ),
    model=UserUsageBucketFilterDTO,
    name="UserUsageBucketFilter",
)
class UserUsageBucketFilter(GQLFilter):
    """Filter for user usage buckets."""

    resource_group: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by scaling group name. Scaling groups define where usage was recorded. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    user_uuid: UUIDFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by user UUID. This filters usage buckets for a specific user. "
            "Supports equals operation for exact match."
        ),
    )
    project_id: UUIDFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by project UUID. This filters usage buckets for users within a specific project. "
            "Supports equals operation for exact match."
        ),
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by domain name. This filters usage buckets for users within a specific domain. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    period_start: DateFilter | None = strawberry.field(
        default=None, description="Filter by usage measurement period start date."
    )
    period_end: DateFilter | None = strawberry.field(
        default=None, description="Filter by usage measurement period end date."
    )

    AND: list[UserUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[UserUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[UserUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    def to_pydantic(self) -> UserUsageBucketFilterDTO:
        return UserUsageBucketFilterDTO(
            resource_group=self.resource_group.to_pydantic() if self.resource_group else None,
            user_uuid=self.user_uuid.to_pydantic() if self.user_uuid else None,
            project_id=self.project_id.to_pydantic() if self.project_id else None,
            domain_name=self.domain_name.to_pydantic() if self.domain_name else None,
            period_start=self.period_start.to_pydantic() if self.period_start else None,
            period_end=self.period_end.to_pydantic() if self.period_end else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for user usage bucket query results. Combine field selection with direction to sort results. Default direction is DESC (most recent first).",
        added_version="26.1.0",
    ),
    model=UserUsageBucketOrderByDTO,
    name="UserUsageBucketOrderBy",
)
class UserUsageBucketOrderBy(GQLOrderBy):
    """OrderBy for user usage buckets."""

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

    def to_pydantic(self) -> UserUsageBucketOrderByDTO:
        return UserUsageBucketOrderByDTO(
            field=UsageBucketOrderFieldDTO(self.field.value),
            direction=OrderDirectionDTO(self.direction.value),
        )


__all__ = [
    "UserUsageBucketGQL",
    "UserUsageBucketConnection",
    "UserUsageBucketEdge",
    "UserUsageBucketFilter",
    "UserUsageBucketOrderBy",
]
