"""Domain Fair Share GQL types, filters, and order-by definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.fair_share.request import (
    BulkUpsertDomainFairShareWeightInput as BulkUpsertDomainFairShareWeightInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareDomainNestedFilter as DomainFairShareDomainNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareFilter as DomainFairShareFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareOrder as DomainFairShareOrderDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainWeightEntryInput as DomainWeightEntryInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UpsertDomainFairShareWeightInput as UpsertDomainFairShareWeightInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload as BulkUpsertDomainFairShareWeightPayloadDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    DomainFairShareNode,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    UpsertDomainFairShareWeightPayload as UpsertDomainFairShareWeightPayloadDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Domain-level fair share data representing scheduling priority for an entire domain. The fair share factor determines resource allocation relative to other domains.",
    ),
    name="DomainFairShare",
)
class DomainFairShareGQL(PydanticNodeMixin[DomainFairShareNode]):
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
        return await info.context.data_loaders.domain_loader.load(self.domain_name)

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
        return await info.context.data_loaders.resource_group_loader.load(self.resource_group_name)


DomainFairShareEdge = Edge[DomainFairShareGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Paginated connection for domain fair share records. "
            "Provides relay-style cursor-based pagination for efficient traversal of domain fair share data. "
            "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
        ),
    )
)
class DomainFairShareConnection(Connection[DomainFairShareGQL]):
    count: int = strawberry.field(
        description="Total number of domain fair share records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for domain entity fields in domain fair share queries. Allows filtering by domain properties such as active status.",
        added_version="26.2.0",
    ),
    name="DomainFairShareDomainNestedFilter",
)
class DomainFairShareDomainNestedFilter(PydanticInputMixin[DomainFairShareDomainNestedFilterDTO]):
    """Nested filter for domain entity within domain fair share."""

    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by domain active status.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying domain fair shares. Supports filtering by scaling group and domain name with various string matching operations. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.1.0",
    ),
    name="DomainFairShareFilter",
)
class DomainFairShareFilter(PydanticInputMixin[DomainFairShareFilterDTO]):
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

    AND: list[Self] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[Self] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[Self] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for domain fair shares within a resource group scope. References resource group membership columns to avoid excluding domains without fair share records.",
        added_version="26.2.0",
    ),
    name="RGDomainFairShareFilter",
)
class RGDomainFairShareFilter(PydanticInputMixin[DomainFairShareFilterDTO]):
    """Filter for domain fair shares in RG context (uses INNER JOIN'd columns)."""

    resource_group: StringFilter | None = strawberry.field(
        default=None, description="Filter by scaling group name."
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None, description="Filter by domain name."
    )
    domain: DomainFairShareDomainNestedFilter | None = strawberry.field(
        default=None, description="Filter by domain properties."
    )

    AND: list[Self] | None = strawberry.field(default=None, description="Combine with AND logic.")
    OR: list[Self] | None = strawberry.field(default=None, description="Combine with OR logic.")
    NOT: list[Self] | None = strawberry.field(default=None, description="Negate filters.")


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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for domain fair share query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.1.0",
    ),
    name="DomainFairShareOrderBy",
)
class DomainFairShareOrderBy(PydanticInputMixin[DomainFairShareOrderDTO]):
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


# Mutation Input/Payload Types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for upserting domain fair share weight. The weight parameter affects scheduling priority - higher weight = higher priority. Set weight to null to use resource group's default_weight.",
        added_version="26.1.0",
    ),
    name="UpsertDomainFairShareWeightInput",
)
class UpsertDomainFairShareWeightInput(PydanticInputMixin[UpsertDomainFairShareWeightInputDTO]):
    """Input for upserting domain fair share weight."""

    resource_group_name: str = strawberry.field(
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for domain fair share weight upsert mutation.",
    ),
    model=UpsertDomainFairShareWeightPayloadDTO,
    name="UpsertDomainFairShareWeightPayload",
)
class UpsertDomainFairShareWeightPayload(
    PydanticOutputMixin[UpsertDomainFairShareWeightPayloadDTO]
):
    """Payload for domain fair share weight upsert mutation."""

    domain_fair_share: DomainFairShareGQL = strawberry.field(
        description="The updated or created domain fair share record."
    )


# Bulk Upsert Mutation Input/Payload Types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input item for a single domain weight in bulk upsert. Represents one domain's weight configuration.",
        added_version="26.1.0",
    ),
    name="DomainWeightInputItem",
)
class DomainWeightInputItem(PydanticInputMixin[DomainWeightEntryInputDTO]):
    """Input item for a single domain weight in bulk upsert."""

    domain_name: str = strawberry.field(description="Name of the domain to update weight for.")
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority allocation ratio. "
            "Set to null to use resource group's default_weight."
        ),
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk upserting domain fair share weights. Allows updating multiple domains in a single transaction.",
        added_version="26.1.0",
    ),
    name="BulkUpsertDomainFairShareWeightInput",
)
class BulkUpsertDomainFairShareWeightInput(
    PydanticInputMixin[BulkUpsertDomainFairShareWeightInputDTO]
):
    """Input for bulk upserting domain fair share weights."""

    resource_group_name: str = strawberry.field(
        description="Name of the scaling group (resource group) for all fair shares."
    )
    inputs: list[DomainWeightInputItem] = strawberry.field(
        description="List of domain weight updates to apply."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for bulk domain fair share weight upsert mutation.",
    ),
    model=BulkUpsertDomainFairShareWeightPayloadDTO,
    all_fields=True,
    name="BulkUpsertDomainFairShareWeightPayload",
)
class BulkUpsertDomainFairShareWeightPayload(
    PydanticOutputMixin[BulkUpsertDomainFairShareWeightPayloadDTO]
):
    pass
