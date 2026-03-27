"""Replica resolver functions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.deployment.request import SearchReplicasInput
from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
    gql_subscription,
)
from ai.backend.manager.api.gql.deployment.types.replica import (
    ModelReplica,
    ModelReplicaConnection,
    ModelReplicaEdge,
    ReplicaFilter,
    ReplicaOrderBy,
    ReplicaStatusChangedPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# Query resolvers


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="List replicas with optional filtering and pagination (admin, all deployments).",
    )
)  # type: ignore[misc]
async def replicas(
    info: Info[StrawberryGQLContext],
    filter: ReplicaFilter | None = None,
    order_by: list[ReplicaOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelReplicaConnection | None:
    """List replicas with optional filtering and pagination (admin, all deployments)."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.admin_search_replicas(
        SearchReplicasInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [ModelReplica.from_pydantic(item) for item in payload.items]
    edges = [ModelReplicaEdge(node=node, cursor=str(node.id)) for node in nodes]
    return ModelReplicaConnection(
        count=payload.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@gql_root_field(
    BackendAIGQLMeta(added_version="25.16.0", description="Get a specific replica by ID.")
)  # type: ignore[misc]
async def replica(id: ID, info: Info[StrawberryGQLContext]) -> ModelReplica | None:
    """Get a specific replica by ID."""
    _, replica_id = resolve_global_id(id)
    node = await info.context.adapters.deployment.get_replica(UUID(replica_id))
    if node is None:
        return None
    return ModelReplica.from_pydantic(node)


# Subscription resolvers


@gql_subscription(
    BackendAIGQLMeta(added_version="25.16.0", description="Subscribe to replica status changes.")
)  # type: ignore[misc]
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    # TODO: Implement actual subscription logic using pub/sub system
    raise NotImplementedError("Subscription not implemented")
    yield  # type: ignore[unreachable]  # Makes this an async generator
