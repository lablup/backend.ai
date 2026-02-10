"""Domain Fair Share GQL types, filters, and order-by definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, override

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.fair_share.types import DomainFairShareData
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.fair_share.options import (
    DomainFairShareConditions,
    DomainFairShareOrders,
)

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
    ResourceSlotGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL


@strawberry.type(
    name="DomainFairShare",
    description="Added in 26.1.0. Domain-level fair share data representing scheduling priority for an entire domain. The fair share factor determines resource allocation relative to other domains.",
)
class DomainFairShareGQL(Node):
    """Domain-level fair share data with calculated fair share factor."""

    id: NodeID[str]
    resource_group_name: str = strawberry.field(
        description="Name of the scaling group this fair share belongs to."
    )
    domain_name: str = strawberry.field(
        description="Name of the domain this fair share is calculated for."
    )
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
        description=("Added in 26.2.0. The domain entity associated with this fair share record.")
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
    def from_dataclass(cls, data: DomainFairShareData) -> DomainFairShareGQL:
        """Convert DomainFairShareData to GraphQL type.

        No async needed - Repository provides complete data.
        Note: metadata can be None for default-generated records.
        """
        return cls(
            id=ID(f"{data.resource_group}:{data.domain_name}"),
            resource_group_name=data.resource_group,
            domain_name=data.domain_name,
            spec=FairShareSpecGQL.from_spec(
                data.data.spec,
                data.data.use_default,
                data.data.uses_default_resources,
            ),
            calculation_snapshot=FairShareCalculationSnapshotGQL(
                fair_share_factor=data.data.calculation_snapshot.fair_share_factor,
                total_decayed_usage=ResourceSlotGQL.from_resource_slot(
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


DomainFairShareEdge = Edge[DomainFairShareGQL]


@strawberry.type(
    description=(
        "Added in 26.1.0. Paginated connection for domain fair share records. "
        "Provides relay-style cursor-based pagination for efficient traversal of domain fair share data. "
        "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
    )
)
class DomainFairShareConnection(Connection[DomainFairShareGQL]):
    count: int = strawberry.field(
        description="Total number of domain fair share records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.input(
    name="DomainFairShareDomainNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for domain entity fields in domain fair share queries. "
        "Allows filtering by domain properties such as active status."
    ),
)
class DomainFairShareDomainNestedFilter:
    """Nested filter for domain entity within domain fair share."""

    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by domain active status.",
    )

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.is_active is not None:
            conditions.append(DomainFairShareConditions.by_domain_is_active(self.is_active))
        return conditions


@strawberry.input(
    name="DomainFairShareFilter",
    description=(
        "Added in 26.1.0. Filter input for querying domain fair shares. "
        "Supports filtering by scaling group and domain name with various string matching operations. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class DomainFairShareFilter(GQLFilter):
    """Filter for domain fair shares."""

    resource_group: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by scaling group name. Scaling groups define resource pool boundaries "
            "where domains compete for resources. Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by domain name. Domains are organizational units containing projects and users. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    domain: DomainFairShareDomainNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Added in 26.2.0. Nested filter for domain entity properties. "
            "Allows filtering by domain active status."
        ),
    )

    AND: list[DomainFairShareFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[DomainFairShareFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[DomainFairShareFilter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.resource_group:
            sg_condition = self.resource_group.build_query_condition(
                contains_factory=lambda spec: DomainFairShareConditions.by_resource_group(
                    spec.value
                ),
                equals_factory=lambda spec: DomainFairShareConditions.by_resource_group(spec.value),
                starts_with_factory=lambda spec: DomainFairShareConditions.by_resource_group(
                    spec.value
                ),
                ends_with_factory=lambda spec: DomainFairShareConditions.by_resource_group(
                    spec.value
                ),
            )
            if sg_condition:
                conditions.append(sg_condition)

        if self.domain_name:
            dn_condition = self.domain_name.build_query_condition(
                contains_factory=lambda spec: DomainFairShareConditions.by_domain_name(spec.value),
                equals_factory=lambda spec: DomainFairShareConditions.by_domain_name(spec.value),
                starts_with_factory=lambda spec: DomainFairShareConditions.by_domain_name(
                    spec.value
                ),
                ends_with_factory=lambda spec: DomainFairShareConditions.by_domain_name(spec.value),
            )
            if dn_condition:
                conditions.append(dn_condition)

        if self.domain:
            conditions.extend(self.domain.build_conditions())

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
    name="DomainFairShareOrderField",
    description=(
        "Added in 26.1.0. Fields available for ordering domain fair share query results. "
        "FAIR_SHARE_FACTOR: Order by the calculated fair share factor (0-1 range, lower = higher priority). "
        "DOMAIN_NAME: Order alphabetically by domain name. "
        "CREATED_AT: Order by record creation timestamp. "
        "DOMAIN_IS_ACTIVE: Order by domain active status (added in 26.2.0)."
    ),
)
class DomainFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    DOMAIN_NAME = "domain_name"
    CREATED_AT = "created_at"
    DOMAIN_IS_ACTIVE = "domain_is_active"


@strawberry.input(
    name="DomainFairShareOrderBy",
    description=(
        "Added in 26.1.0. Specifies ordering for domain fair share query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class DomainFairShareOrderBy(GQLOrderBy):
    """OrderBy for domain fair shares."""

    field: DomainFairShareOrderField = strawberry.field(
        description="The field to order by. See DomainFairShareOrderField for available options."
    )
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description=(
            "Sort direction. ASC for ascending (lowest first), DESC for descending (highest first). "
            "For fair_share_factor, ASC shows highest priority domains first."
        ),
    )

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case DomainFairShareOrderField.FAIR_SHARE_FACTOR:
                return DomainFairShareOrders.by_fair_share_factor(ascending)
            case DomainFairShareOrderField.DOMAIN_NAME:
                return DomainFairShareOrders.by_domain_name(ascending)
            case DomainFairShareOrderField.CREATED_AT:
                return DomainFairShareOrders.by_created_at(ascending)
            case DomainFairShareOrderField.DOMAIN_IS_ACTIVE:
                return DomainFairShareOrders.by_domain_is_active(ascending)


# Mutation Input/Payload Types


@strawberry.input(
    name="UpsertDomainFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for upserting domain fair share weight. "
        "The weight parameter affects scheduling priority - higher weight = higher priority. "
        "Set weight to null to use resource group's default_weight."
    ),
)
class UpsertDomainFairShareWeightInput:
    """Input for upserting domain fair share weight."""

    resource_group: str = strawberry.field(
        description="Name of the scaling group (resource group) for this fair share."
    )
    domain_name: str = strawberry.field(description="Name of the domain to update weight for.")
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority allocation ratio. "
            "Set to null to use resource group's default_weight."
        ),
    )


@strawberry.type(
    name="UpsertDomainFairShareWeightPayload",
    description="Added in 26.1.0. Payload for domain fair share weight upsert mutation.",
)
class UpsertDomainFairShareWeightPayload:
    """Payload for domain fair share weight upsert mutation."""

    domain_fair_share: DomainFairShareGQL = strawberry.field(
        description="The updated or created domain fair share record."
    )


# Bulk Upsert Mutation Input/Payload Types


@strawberry.input(
    name="DomainWeightInputItem",
    description=(
        "Added in 26.1.0. Input item for a single domain weight in bulk upsert. "
        "Represents one domain's weight configuration."
    ),
)
class DomainWeightInputItem:
    """Input item for a single domain weight in bulk upsert."""

    domain_name: str = strawberry.field(description="Name of the domain to update weight for.")
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority allocation ratio. "
            "Set to null to use resource group's default_weight."
        ),
    )


@strawberry.input(
    name="BulkUpsertDomainFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for bulk upserting domain fair share weights. "
        "Allows updating multiple domains in a single transaction."
    ),
)
class BulkUpsertDomainFairShareWeightInput:
    """Input for bulk upserting domain fair share weights."""

    resource_group: str = strawberry.field(
        description="Name of the scaling group (resource group) for all fair shares."
    )
    inputs: list[DomainWeightInputItem] = strawberry.field(
        description="List of domain weight updates to apply."
    )


@strawberry.type(
    name="BulkUpsertDomainFairShareWeightPayload",
    description="Added in 26.1.0. Payload for bulk domain fair share weight upsert mutation.",
)
class BulkUpsertDomainFairShareWeightPayload:
    """Payload for bulk domain fair share weight upsert mutation."""

    upserted_count: int = strawberry.field(
        description="Number of domain fair share records created or updated."
    )
