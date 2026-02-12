"""Project Fair Share GQL types, filters, and order-by definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.fair_share.types import ProjectFairShareData
from ai.backend.manager.data.group.types import ProjectType
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

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL


@strawberry.type(
    name="ProjectFairShare",
    description="Added in 26.1.0. Project-level fair share data representing scheduling priority for a specific project. The fair share factor determines resource allocation relative to other projects in the same domain.",
)
class ProjectFairShareGQL(Node):
    """Project-level fair share data with calculated fair share factor."""

    id: NodeID[str]
    resource_group_name: str = strawberry.field(
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

    @strawberry.field(  # type: ignore[misc]
        description=("Added in 26.2.0. The project entity associated with this fair share record.")
    )
    async def project(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ProjectV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.node"),
        ]
        | None
    ):
        from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL

        project_data = await info.context.data_loaders.project_loader.load(self.project_id)
        if project_data is None:
            return None
        return ProjectV2GQL.from_data(project_data)

    @strawberry.field(  # type: ignore[misc]
        description=("Added in 26.2.0. The domain entity associated with this fair share record."),
    )
    async def domain(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            DomainV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
        ]
        | None
    ):
        from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL

        domain_data = await info.context.data_loaders.domain_loader.load(self.domain_name)
        if domain_data is None:
            return None
        return DomainV2GQL.from_data(domain_data)

    @strawberry.field(  # type: ignore[misc]
        description=("Added in 26.2.0. The resource group associated with this fair share record."),
    )
    async def resource_group(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ResourceGroupGQL,
            strawberry.lazy("ai.backend.manager.api.gql.resource_group.types"),
        ]
        | None
    ):
        from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL

        rg_data = await info.context.data_loaders.resource_group_loader.load(
            self.resource_group_name
        )
        if rg_data is None:
            return None
        return ResourceGroupGQL.from_dataclass(rg_data)

    @classmethod
    def from_dataclass(cls, data: ProjectFairShareData) -> ProjectFairShareGQL:
        """Convert ProjectFairShareData to GraphQL type.

        No async needed - Repository provides complete data.
        Note: metadata can be None for default-generated records.
        """
        return cls(
            id=ID(f"{data.resource_group}:{data.project_id}"),
            resource_group_name=data.resource_group,
            project_id=data.project_id,
            domain_name=data.domain_name,
            spec=FairShareSpecGQL.from_spec(
                data.data.spec,
                data.data.use_default,
                data.data.uses_default_resources,
            ),
            calculation_snapshot=FairShareCalculationSnapshotGQL(
                fair_share_factor=data.data.calculation_snapshot.fair_share_factor,
                total_decayed_usage=ResourceSlotGQL.from_slot_quantities(
                    data.data.calculation_snapshot.total_decayed_usage
                ),
                normalized_usage=data.data.calculation_snapshot.normalized_usage,
                lookback_start=data.data.calculation_snapshot.lookback_start,
                lookback_end=data.data.calculation_snapshot.lookback_end,
                last_calculated_at=data.data.calculation_snapshot.last_calculated_at,
            ),
            created_at=(
                data.data.metadata.created_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
            updated_at=(
                data.data.metadata.updated_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
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


@strawberry.enum(
    name="ProjectFairShareTypeEnum",
    description="Added in 26.2.0. Project type enum for fair share filtering.",
)
class ProjectFairShareTypeEnum(StrEnum):
    """Project type enum for fair share context."""

    GENERAL = "general"
    MODEL_STORE = "model-store"


@strawberry.input(
    name="ProjectFairShareTypeEnumFilter",
    description=(
        "Added in 26.2.0. Filter for project type enum in fair share queries. "
        "Supports equals, in, not_equals, and not_in operations."
    ),
)
class ProjectFairShareTypeEnumFilter:
    """Filter for project type enum fields in fair share context."""

    equals: ProjectFairShareTypeEnum | None = strawberry.field(
        default=None,
        description="Exact match for project type.",
    )
    in_: list[ProjectFairShareTypeEnum] | None = strawberry.field(
        name="in",
        default=None,
        description="Match any of the provided types.",
    )
    not_equals: ProjectFairShareTypeEnum | None = strawberry.field(
        default=None,
        description="Exclude exact type match.",
    )
    not_in: list[ProjectFairShareTypeEnum] | None = strawberry.field(
        default=None,
        description="Exclude any of the provided types.",
    )


@strawberry.input(
    name="ProjectFairShareProjectNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for project entity fields in project fair share queries. "
        "Allows filtering by project properties such as name, active status, and type."
    ),
)
class ProjectFairShareProjectNestedFilter:
    """Nested filter for project entity within project fair share."""

    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by project name. Supports equals, contains, startsWith, and endsWith.",
    )
    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by project active status.",
    )
    type: ProjectFairShareTypeEnumFilter | None = strawberry.field(
        default=None,
        description="Filter by project type (GENERAL, MODEL_STORE).",
    )

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=lambda spec: ProjectFairShareConditions.by_project_name_contains(
                    spec.value
                ),
                equals_factory=lambda spec: ProjectFairShareConditions.by_project_name_equals(
                    spec.value
                ),
                starts_with_factory=lambda spec: ProjectFairShareConditions.by_project_name_starts_with(
                    spec.value
                ),
                ends_with_factory=lambda spec: ProjectFairShareConditions.by_project_name_ends_with(
                    spec.value
                ),
            )
            if name_condition:
                conditions.append(name_condition)
        if self.is_active is not None:
            conditions.append(ProjectFairShareConditions.by_project_is_active(self.is_active))
        if self.type:
            if self.type.equals is not None:
                conditions.append(
                    ProjectFairShareConditions.by_project_type_equals(
                        ProjectType(self.type.equals.value)
                    )
                )
            if self.type.in_ is not None:
                conditions.append(
                    ProjectFairShareConditions.by_project_type_in([
                        ProjectType(t.value) for t in self.type.in_
                    ])
                )
            if self.type.not_equals is not None:
                conditions.append(
                    negate_conditions([
                        ProjectFairShareConditions.by_project_type_equals(
                            ProjectType(self.type.not_equals.value)
                        )
                    ])
                )
            if self.type.not_in is not None:
                conditions.append(
                    negate_conditions([
                        ProjectFairShareConditions.by_project_type_in([
                            ProjectType(t.value) for t in self.type.not_in
                        ])
                    ])
                )
        return conditions


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
    project: ProjectFairShareProjectNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Added in 26.2.0. Nested filter for project entity properties. "
            "Allows filtering by project name, active status, and type."
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
                contains_factory=lambda spec: ProjectFairShareConditions.by_resource_group_contains(
                    spec.value
                ),
                equals_factory=lambda spec: ProjectFairShareConditions.by_resource_group_equals(
                    spec.value
                ),
                starts_with_factory=lambda spec: ProjectFairShareConditions.by_resource_group_starts_with(
                    spec.value
                ),
                ends_with_factory=lambda spec: ProjectFairShareConditions.by_resource_group_ends_with(
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
                contains_factory=lambda spec: ProjectFairShareConditions.by_domain_name_contains(
                    spec.value
                ),
                equals_factory=lambda spec: ProjectFairShareConditions.by_domain_name_equals(
                    spec.value
                ),
                starts_with_factory=lambda spec: ProjectFairShareConditions.by_domain_name_starts_with(
                    spec.value
                ),
                ends_with_factory=lambda spec: ProjectFairShareConditions.by_domain_name_ends_with(
                    spec.value
                ),
            )
            if dn_condition:
                conditions.append(dn_condition)

        if self.project:
            conditions.extend(self.project.build_conditions())

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
        "CREATED_AT: Order by record creation timestamp. "
        "PROJECT_NAME: Order alphabetically by project name (added in 26.2.0). "
        "PROJECT_IS_ACTIVE: Order by project active status (added in 26.2.0)."
    ),
)
class ProjectFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"
    PROJECT_NAME = "project_name"
    PROJECT_IS_ACTIVE = "project_is_active"


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
            case ProjectFairShareOrderField.PROJECT_NAME:
                return ProjectFairShareOrders.by_project_name(ascending)
            case ProjectFairShareOrderField.PROJECT_IS_ACTIVE:
                return ProjectFairShareOrders.by_project_is_active(ascending)


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

    resource_group_name: str = strawberry.field(
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

    resource_group_name: str = strawberry.field(
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
