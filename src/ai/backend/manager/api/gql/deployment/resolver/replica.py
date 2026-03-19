"""Replica resolver functions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.deployment.request import SearchReplicasInput
from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.deployment.types.replica import (
    ModelReplica,
    ModelReplicaConnection,
    ModelReplicaEdge,
    ReplicaFilter,
    ReplicaOrderBy,
    ReplicaStatusChangedPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
)

# Query resolvers


@strawberry.field(description="Added in 25.16.0")  # type: ignore[misc]
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
    nodes = [ModelReplica.from_node(item) for item in payload.items]
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


@strawberry.field(description="Added in 25.16.0")  # type: ignore[misc]
async def replica(id: ID, info: Info[StrawberryGQLContext]) -> ModelReplica | None:
    """Get a specific replica by ID."""
    _, replica_id = resolve_global_id(id)
    processor = info.context.processors.deployment
    result = await processor.get_replica_by_id.wait_for_complete(
        GetReplicaByIdAction(replica_id=UUID(replica_id))
    )
    if result.data is None:
        return None
    return ModelReplica.from_dataclass(result.data)


# Subscription resolvers


@strawberry.subscription(description="Added in 25.16.0")  # type: ignore[misc]
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    # TODO: Implement actual subscription logic using pub/sub system
    raise NotImplementedError("Subscription not implemented")
    yield  # type: ignore[unreachable]  # Makes this an async generator
