"""Replica resolver functions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.deployment.fetcher.replica import fetch_replicas
from ai.backend.manager.api.gql.deployment.types.replica import (
    ModelReplica,
    ModelReplicaConnection,
    ReplicaFilter,
    ReplicaOrderBy,
    ReplicaStatusChangedPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
)

# Query resolvers


@strawberry.field(description="Added in 25.16.0")
async def replicas(
    info: Info[StrawberryGQLContext],
    filter: Optional[ReplicaFilter] = None,
    order_by: Optional[list[ReplicaOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelReplicaConnection:
    """List replicas with optional filtering and pagination."""
    return await fetch_replicas(
        info=info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field(description="Added in 25.16.0")
async def replica(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ModelReplica]:
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


@strawberry.subscription(description="Added in 25.16.0")
async def replica_status_changed(
    revision_id: ID,
) -> AsyncGenerator[ReplicaStatusChangedPayload, None]:
    """Subscribe to replica status changes."""
    # TODO: Implement actual subscription logic using pub/sub system
    if False:  # Placeholder to satisfy type checker
        yield ReplicaStatusChangedPayload(replica=ModelReplica())
