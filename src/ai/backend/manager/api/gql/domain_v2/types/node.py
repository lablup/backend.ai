"""DomainV2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainFairShareScopeDTO,
    DomainUsageScopeDTO,
)
from ai.backend.manager.api.gql.fair_share.types import DomainFairShareGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.resource_slot.overview_types import ActiveResourceOverviewGQL
from ai.backend.manager.api.gql.resource_usage.types import (
    DomainUsageBucketConnection,
    DomainUsageBucketFilter,
    DomainUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .nested import (
    DomainBasicInfoGQL,
    DomainLifecycleInfoGQL,
    DomainRegistryInfoGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.project_v2.types.filters import (
        ProjectV2Filter,
        ProjectV2OrderBy,
    )
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2Connection
    from ai.backend.manager.api.gql.user.types.filters import UserFilterGQL, UserOrderByGQL
    from ai.backend.manager.api.gql.user.types.node import UserV2Connection
    from ai.backend.manager.data.domain.types import DomainData


@strawberry.experimental.pydantic.input(
    model=DomainFairShareScopeDTO,
    name="DomainFairShareScope",
)
class DomainFairShareScopeGQL:
    """Scope parameters for filtering domain fair shares."""

    resource_group_name: str = strawberry.field(
        description="Resource group to filter fair shares by."
    )

    def to_pydantic(self) -> DomainFairShareScopeDTO:
        return DomainFairShareScopeDTO(resource_group_name=self.resource_group_name)


@strawberry.experimental.pydantic.input(
    model=DomainUsageScopeDTO,
    name="DomainUsageScope",
)
class DomainUsageScopeGQL:
    """Scope parameters for filtering domain usage buckets."""

    resource_group_name: str = strawberry.field(
        description="Resource group to filter usage buckets by."
    )

    def to_pydantic(self) -> DomainUsageScopeDTO:
        return DomainUsageScopeDTO(resource_group_name=self.resource_group_name)


@strawberry.federation.type(
    keys=["id"],
    name="DomainV2",
    description=(
        "Added in 26.2.0. Domain entity with structured field groups. "
        "Formerly DomainNode. Provides comprehensive domain information organized "
        "into logical categories: basic_info (identity), registry (container registries), "
        "and lifecycle (status/timestamps). "
        "All fields use typed structures instead of JSON scalars. "
        "Resource allocation and storage permissions are provided through separate dedicated APIs."
    ),
)
class DomainV2GQL(PydanticNodeMixin[DomainNode]):
    """Domain entity with structured field groups."""

    id: NodeID[str] = strawberry.field(description="Domain name (primary key).")
    basic_info: DomainBasicInfoGQL = strawberry.field(
        description="Basic domain information including name and description."
    )
    registry: DomainRegistryInfoGQL = strawberry.field(
        description="Container registry configuration."
    )
    lifecycle: DomainLifecycleInfoGQL = strawberry.field(
        description="Lifecycle information including activation status and timestamps."
    )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Fair share record for this domain in the specified resource group. "
            "Returns the scheduling priority configuration for this domain. "
            "Always returns an object, even if no explicit configuration exists "
            "(in which case default values are used)."
        )
    )
    async def fair_share(
        self,
        info: Info,
        scope: DomainFairShareScopeGQL,
    ) -> DomainFairShareGQL:
        from ai.backend.common.dto.manager.v2.fair_share.request import GetDomainFairShareInput

        payload = await info.context.adapters.fair_share.get_domain(
            GetDomainFairShareInput(
                resource_group=scope.resource_group_name,
                domain_name=str(self.id),
            )
        )

        return DomainFairShareGQL.from_pydantic(payload.item)

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.4.0. Active resource usage overview for this domain. "
            "Returns the currently occupied resource slots and the number of active sessions."
        )
    )
    async def active_resource_overview(
        self,
        info: Info,
    ) -> ActiveResourceOverviewGQL:
        from ai.backend.manager.services.resource_slot.actions.get_domain_resource_overview import (
            GetDomainResourceOverviewAction,
        )

        result = await info.context.processors.resource_slot.get_domain_resource_overview.wait_for_complete(
            GetDomainResourceOverviewAction(domain_name=str(self.id))
        )
        return ActiveResourceOverviewGQL.from_occupancy(result.item)

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Usage buckets for this domain, filtered by resource group. "
            "Returns aggregated resource usage statistics over time."
        )
    )
    async def usage_buckets(
        self,
        info: Info,
        scope: DomainUsageScopeGQL,
        filter: DomainUsageBucketFilter | None = None,
        order_by: list[DomainUsageBucketOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> DomainUsageBucketConnection:
        from strawberry.relay import PageInfo

        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.resource_usage.types import (
            DomainUsageBucketEdge,
            DomainUsageBucketGQL,
        )
        from ai.backend.manager.repositories.resource_usage_history.types import (
            DomainUsageBucketSearchScope,
        )

        repository_scope = DomainUsageBucketSearchScope(
            resource_group=scope.resource_group_name,
            domain_name=str(self.id),
        )

        payload = await info.context.adapters.resource_usage.gql_search_domain_scoped(
            scope=repository_scope,
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )

        nodes = [DomainUsageBucketGQL.from_pydantic(item) for item in payload.items]
        edges = [
            DomainUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
        ]

        return DomainUsageBucketConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @strawberry.field(  # type: ignore[misc]
        description="Projects belonging to this domain.",
    )
    async def projects(
        self,
        info: Info,
        filter: Annotated[
            ProjectV2Filter, strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.filters")
        ]
        | None = None,
        order_by: list[
            Annotated[
                ProjectV2OrderBy,
                strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.filters"),
            ]
        ]
        | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Annotated[
        ProjectV2Connection,
        strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.node"),
    ]:
        from strawberry.relay import PageInfo

        from ai.backend.common.dto.manager.v2.group.request import AdminSearchGroupsInput
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.project_v2.types.node import (
            ProjectV2Connection,
            ProjectV2Edge,
            ProjectV2GQL,
        )
        from ai.backend.manager.repositories.group.types import DomainProjectSearchScope

        scope = DomainProjectSearchScope(domain_name=str(self.id))
        payload = await info.context.adapters.project.search_by_domain(
            scope=scope,
            input=AdminSearchGroupsInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [ProjectV2GQL.from_pydantic(node) for node in payload.items]
        edges = [ProjectV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return ProjectV2Connection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @strawberry.field(  # type: ignore[misc]
        description="Users belonging to this domain.",
    )
    async def users(
        self,
        info: Info,
        filter: Annotated[
            UserFilterGQL, strawberry.lazy("ai.backend.manager.api.gql.user.types.filters")
        ]
        | None = None,
        order_by: list[
            Annotated[
                UserOrderByGQL,
                strawberry.lazy("ai.backend.manager.api.gql.user.types.filters"),
            ]
        ]
        | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Annotated[
        UserV2Connection,
        strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
    ]:
        from strawberry.relay import PageInfo

        from ai.backend.common.dto.manager.v2.user.request import AdminSearchUsersInput
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.user.types.node import (
            UserV2Connection,
            UserV2Edge,
            UserV2GQL,
        )
        from ai.backend.manager.repositories.user.types import DomainUserSearchScope

        scope = DomainUserSearchScope(domain_name=str(self.id))
        payload = await info.context.adapters.user.gql_search_by_domain(
            scope=scope,
            input=AdminSearchUsersInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [UserV2GQL.from_pydantic(item) for item in payload.items]
        edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return UserV2Connection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.domain_loader.load_many(node_ids)
        return [cls.from_data(data) if data is not None else None for data in results]

    @classmethod
    def from_pydantic(
        cls,
        dto: DomainNode,
        *,
        id_field: str = "id",
        extra: dict[str, Any] | None = None,
    ) -> Self:
        """Create DomainV2GQL from DomainNode DTO (adapter search results)."""
        return cls(
            id=ID(dto.id),
            basic_info=DomainBasicInfoGQL(
                name=dto.basic_info.name,
                description=dto.basic_info.description,
                integration_id=dto.basic_info.integration_id,
            ),
            registry=DomainRegistryInfoGQL(
                allowed_docker_registries=dto.registry.allowed_docker_registries,
            ),
            lifecycle=DomainLifecycleInfoGQL(
                is_active=dto.lifecycle.is_active,
                created_at=dto.lifecycle.created_at,
                modified_at=dto.lifecycle.modified_at,
            ),
        )

    @classmethod
    def from_data(
        cls,
        data: DomainData,
    ) -> Self:
        """Convert DomainData to GraphQL type.

        Args:
            data: DomainData instance from the data layer.

        Returns:
            DomainV2GQL instance with structured field groups.

        Note:
            - All fields are directly from DomainRow (no external lookups)
            - No JSON scalars are used in the output
            - Primary key is domain name (string), not UUID
            - ResourceSlot and storage permissions are excluded; use dedicated APIs
            - Dotfiles (binary data) is excluded; use query_domain_dotfiles()
        """
        return cls(
            id=ID(data.name),  # name is the primary key
            basic_info=DomainBasicInfoGQL(
                name=data.name,
                description=data.description,
                integration_id=data.integration_id,
            ),
            registry=DomainRegistryInfoGQL(
                allowed_docker_registries=data.allowed_docker_registries,
            ),
            lifecycle=DomainLifecycleInfoGQL(
                is_active=data.is_active,
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )


DomainV2Edge = Edge[DomainV2GQL]


@strawberry.type(
    description=(
        "Added in 26.2.0. Paginated connection for domain records. "
        "Provides relay-style cursor-based pagination for efficient traversal of domain data. "
        "Use 'edges' to access individual records with cursor information, "
        "or 'nodes' for direct data access."
    )
)
class DomainV2Connection(Connection[DomainV2GQL]):
    """Paginated connection for domain records."""

    count: int = strawberry.field(
        description="Total number of domain records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
