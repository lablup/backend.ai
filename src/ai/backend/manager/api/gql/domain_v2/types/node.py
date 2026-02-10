"""DomainV2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.fair_share.types import DomainFairShareGQL
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
    from ai.backend.manager.api.gql.user_v2.types.filters import UserV2Filter, UserV2OrderBy
    from ai.backend.manager.api.gql.user_v2.types.node import UserV2Connection
    from ai.backend.manager.data.domain.types import DomainData


@strawberry.input(name="DomainFairShareScope")
class DomainFairShareScopeGQL:
    """Scope parameters for filtering domain fair shares."""

    resource_group: str = strawberry.field(description="Resource group to filter fair shares by.")


@strawberry.input(name="DomainUsageScope")
class DomainUsageScopeGQL:
    """Scope parameters for filtering domain usage buckets."""

    resource_group: str = strawberry.field(description="Resource group to filter usage buckets by.")


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
class DomainV2GQL(Node):
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
        from ai.backend.manager.api.gql.fair_share.fetcher.domain import (
            fetch_single_domain_fair_share,
        )

        return await fetch_single_domain_fair_share(
            info=info,
            resource_group=scope.resource_group,
            domain_name=str(self.id),
        )

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
        from ai.backend.manager.api.gql.resource_usage.fetcher.domain_usage import (
            fetch_rg_domain_usage_buckets,
        )
        from ai.backend.manager.repositories.resource_usage_history.types import (
            DomainUsageBucketSearchScope,
        )

        # Create repository scope with context information
        repository_scope = DomainUsageBucketSearchScope(
            resource_group=scope.resource_group,
            domain_name=str(self.id),
        )

        # No additional filters needed (scope includes all entity info)
        base_conditions = None

        return await fetch_rg_domain_usage_buckets(
            info=info,
            scope=repository_scope,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=base_conditions,
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
        from ai.backend.manager.api.gql.project_v2.fetcher.project import (
            fetch_domain_projects,
        )
        from ai.backend.manager.repositories.group.types import DomainProjectSearchScope

        scope = DomainProjectSearchScope(domain_name=str(self.id))
        return await fetch_domain_projects(
            info=info,
            scope=scope,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )

    @strawberry.field(  # type: ignore[misc]
        description="Users belonging to this domain.",
    )
    async def users(
        self,
        info: Info,
        filter: Annotated[
            UserV2Filter, strawberry.lazy("ai.backend.manager.api.gql.user_v2.types.filters")
        ]
        | None = None,
        order_by: list[
            Annotated[
                UserV2OrderBy,
                strawberry.lazy("ai.backend.manager.api.gql.user_v2.types.filters"),
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
        strawberry.lazy("ai.backend.manager.api.gql.user_v2.types.node"),
    ]:
        from ai.backend.manager.api.gql.user_v2.fetcher.user import fetch_domain_users
        from ai.backend.manager.repositories.user.types import DomainUserSearchScope

        scope = DomainUserSearchScope(domain_name=str(self.id))
        return await fetch_domain_users(
            info=info,
            scope=scope,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
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
