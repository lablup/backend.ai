"""Project Fair Share GQL types, filters, and order-by definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.fair_share.types import ProjectFairShareData
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.fair_share.options import (
    ProjectFairShareConditions,
    ProjectFairShareOrders,
)

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
    ResourceSlotGQL,
)
from .user import (
    UserFairShareConnection,
    UserFairShareFilter,
    UserFairShareOrderBy,
)


@strawberry.type(
    name="ProjectFairShare",
    description="Added in 26.1.0. Project-level fair share data representing scheduling priority for a specific project. The fair share factor determines resource allocation relative to other projects in the same domain.",
)
class ProjectFairShareGQL(Node):
    """Project-level fair share data with calculated fair share factor."""

    id: NodeID[str]
    resource_group: str = strawberry.field(
        description="Name of the scaling group this fair share belongs to."
    )
    project_id: UUID = strawberry.field(
        description="UUID of the project this fair share is calculated for."
    )
    domain_name: str = strawberry.field(description="Name of the domain the project belongs to.")
    spec: FairShareSpecGQL = strawberry.field(
        description="Fair share specification parameters used for calculation."
    )
    calculation_snapshot: FairShareCalculationSnapshotGQL = strawberry.field(
        description="Snapshot of the most recent fair share calculation results."
    )
    created_at: datetime = strawberry.field(description="Timestamp when this record was created.")
    updated_at: datetime = strawberry.field(
        description="Timestamp when this record was last updated."
    )

    @strawberry.field(
        description=(
            "Added in 26.1.0. List user fair shares belonging to this project. "
            "Returns fair share data for all users within this project and scaling group."
        )
    )
    async def user_fair_shares(
        self,
        info: Info,
        filter: UserFairShareFilter | None = None,
        order_by: list[UserFairShareOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> UserFairShareConnection:
        from ai.backend.manager.api.gql.fair_share.fetcher import fetch_user_fair_shares
        from ai.backend.manager.repositories.fair_share.options import UserFairShareConditions

        return await fetch_user_fair_shares(
            info=info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=[
                UserFairShareConditions.by_resource_group(self.resource_group),
                UserFairShareConditions.by_project_id(self.project_id),
            ],
        )

    @classmethod
    def from_dataclass(cls, data: ProjectFairShareData) -> ProjectFairShareGQL:
        return cls(
            id=ID(str(data.id)),
            resource_group=data.resource_group,
            project_id=data.project_id,
            domain_name=data.domain_name,
            spec=FairShareSpecGQL.from_spec(data.spec, data.default_weight),
            calculation_snapshot=FairShareCalculationSnapshotGQL(
                fair_share_factor=data.calculation_snapshot.fair_share_factor,
                total_decayed_usage=ResourceSlotGQL.from_resource_slot(
                    data.calculation_snapshot.total_decayed_usage
                ),
                normalized_usage=data.calculation_snapshot.normalized_usage,
                lookback_start=data.calculation_snapshot.lookback_start,
                lookback_end=data.calculation_snapshot.lookback_end,
                last_calculated_at=data.calculation_snapshot.last_calculated_at,
            ),
            created_at=data.metadata.created_at,
            updated_at=data.metadata.updated_at,
        )


ProjectFairShareEdge = Edge[ProjectFairShareGQL]


@strawberry.type(
    description=(
        "Added in 26.1.0. Paginated connection for project fair share records. "
        "Provides relay-style cursor-based pagination for efficient traversal of project fair share data. "
        "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
    )
)
class ProjectFairShareConnection(Connection[ProjectFairShareGQL]):
    count: int = strawberry.field(
        description="Total number of project fair share records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.input(
    name="ProjectFairShareFilter",
    description=(
        "Added in 26.1.0. Filter input for querying project fair shares. "
        "Supports filtering by scaling group, project ID, and domain name. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class ProjectFairShareFilter(GQLFilter):
    """Filter for project fair shares."""

    resource_group: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by scaling group name. Scaling groups define resource pool boundaries "
            "where projects compete for resources within their domain. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    project_id: UUIDFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by project UUID. Projects are containers for sessions and user activities. "
            "Supports equals operation for exact match or 'in' operation for multiple UUIDs."
        ),
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by domain name. This filters projects belonging to a specific domain. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )

    AND: list[ProjectFairShareFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[ProjectFairShareFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[ProjectFairShareFilter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.resource_group:
            sg_condition = self.resource_group.build_query_condition(
                contains_factory=lambda spec: ProjectFairShareConditions.by_resource_group(
                    spec.value
                ),
                equals_factory=lambda spec: ProjectFairShareConditions.by_resource_group(
                    spec.value
                ),
                starts_with_factory=lambda spec: ProjectFairShareConditions.by_resource_group(
                    spec.value
                ),
                ends_with_factory=lambda spec: ProjectFairShareConditions.by_resource_group(
                    spec.value
                ),
            )
            if sg_condition:
                conditions.append(sg_condition)

        if self.project_id:
            pid_condition = self.project_id.build_query_condition(
                equals_factory=lambda spec: ProjectFairShareConditions.by_project_id(spec.value),
                in_factory=lambda spec: ProjectFairShareConditions.by_project_ids(spec.values),
            )
            if pid_condition:
                conditions.append(pid_condition)

        if self.domain_name:
            dn_condition = self.domain_name.build_query_condition(
                contains_factory=lambda spec: ProjectFairShareConditions.by_domain_name(spec.value),
                equals_factory=lambda spec: ProjectFairShareConditions.by_domain_name(spec.value),
                starts_with_factory=lambda spec: ProjectFairShareConditions.by_domain_name(
                    spec.value
                ),
                ends_with_factory=lambda spec: ProjectFairShareConditions.by_domain_name(
                    spec.value
                ),
            )
            if dn_condition:
                conditions.append(dn_condition)

        if self.AND:
            for sub_filter in self.AND:
                conditions.extend(sub_filter.build_conditions())

        if self.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_conditions.extend(sub_filter.build_conditions())
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))

        if self.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_conditions.extend(sub_filter.build_conditions())
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

        return conditions


@strawberry.enum(
    name="ProjectFairShareOrderField",
    description=(
        "Added in 26.1.0. Fields available for ordering project fair share query results. "
        "FAIR_SHARE_FACTOR: Order by the calculated fair share factor (0-1 range, lower = higher priority). "
        "CREATED_AT: Order by record creation timestamp."
    ),
)
class ProjectFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"


@strawberry.input(
    name="ProjectFairShareOrderBy",
    description=(
        "Added in 26.1.0. Specifies ordering for project fair share query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class ProjectFairShareOrderBy(GQLOrderBy):
    """OrderBy for project fair shares."""

    field: ProjectFairShareOrderField = strawberry.field(
        description="The field to order by. See ProjectFairShareOrderField for available options."
    )
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description=(
            "Sort direction. ASC for ascending (lowest first), DESC for descending (highest first). "
            "For fair_share_factor, ASC shows highest priority projects first."
        ),
    )

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ProjectFairShareOrderField.FAIR_SHARE_FACTOR:
                return ProjectFairShareOrders.by_fair_share_factor(ascending)
            case ProjectFairShareOrderField.CREATED_AT:
                return ProjectFairShareOrders.by_created_at(ascending)


# Mutation Input/Payload Types


@strawberry.input(
    name="UpsertProjectFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for upserting project fair share weight. "
        "The weight parameter affects scheduling priority - higher weight = higher priority. "
        "Set weight to null to use resource group's default_weight."
    ),
)
class UpsertProjectFairShareWeightInput:
    """Input for upserting project fair share weight."""

    resource_group: str = strawberry.field(
        description="Name of the scaling group (resource group) for this fair share."
    )
    project_id: UUID = strawberry.field(description="UUID of the project to update weight for.")
    domain_name: str = strawberry.field(description="Name of the domain the project belongs to.")
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority allocation ratio. "
            "Set to null to use resource group's default_weight."
        ),
    )


@strawberry.type(
    name="UpsertProjectFairShareWeightPayload",
    description="Added in 26.1.0. Payload for project fair share weight upsert mutation.",
)
class UpsertProjectFairShareWeightPayload:
    """Payload for project fair share weight upsert mutation."""

    project_fair_share: ProjectFairShareGQL = strawberry.field(
        description="The updated or created project fair share record."
    )


# Bulk Upsert Mutation Input/Payload Types


@strawberry.input(
    name="ProjectWeightInputItem",
    description=(
        "Added in 26.1.0. Input item for a single project weight in bulk upsert. "
        "Represents one project's weight configuration."
    ),
)
class ProjectWeightInputItem:
    """Input item for a single project weight in bulk upsert."""

    project_id: UUID = strawberry.field(description="ID of the project to update weight for.")
    domain_name: str = strawberry.field(description="Name of the domain this project belongs to.")
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority allocation ratio. "
            "Set to null to use resource group's default_weight."
        ),
    )


@strawberry.input(
    name="BulkUpsertProjectFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for bulk upserting project fair share weights. "
        "Allows updating multiple projects in a single transaction."
    ),
)
class BulkUpsertProjectFairShareWeightInput:
    """Input for bulk upserting project fair share weights."""

    resource_group: str = strawberry.field(
        description="Name of the scaling group (resource group) for all fair shares."
    )
    inputs: list[ProjectWeightInputItem] = strawberry.field(
        description="List of project weight updates to apply."
    )


@strawberry.type(
    name="BulkUpsertProjectFairShareWeightPayload",
    description="Added in 26.1.0. Payload for bulk project fair share weight upsert mutation.",
)
class BulkUpsertProjectFairShareWeightPayload:
    """Payload for bulk project fair share weight upsert mutation."""

    upserted_count: int = strawberry.field(
        description="Number of project fair share records created or updated."
    )
