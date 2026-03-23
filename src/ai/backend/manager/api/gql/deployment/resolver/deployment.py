"""Deployment resolver functions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.deployment.request import AdminSearchDeploymentsInput
from ai.backend.manager.api.gql.base import encode_cursor, resolve_global_id
from ai.backend.manager.api.gql.deployment.types.deployment import (
    CreateDeploymentInput,
    CreateDeploymentPayload,
    DeleteDeploymentInput,
    DeleteDeploymentPayload,
    DeploymentFilter,
    DeploymentOrderBy,
    DeploymentStatusChangedPayload,
    ModelDeployment,
    ModelDeploymentConnection,
    ModelDeploymentEdge,
    SyncReplicaInput,
    SyncReplicaPayload,
    UpdateDeploymentInput,
    UpdateDeploymentPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.user import UserNotFound

# Query resolvers


@strawberry.field(description="Added in 25.16.0")  # type: ignore[misc]
async def deployments(
    info: Info[StrawberryGQLContext],
    filter: DeploymentFilter | None = None,
    order_by: list[DeploymentOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelDeploymentConnection | None:
    """List deployments with optional filtering and pagination (admin, all deployments)."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.admin_search(
        AdminSearchDeploymentsInput(
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
    nodes = [ModelDeployment.from_pydantic(item) for item in payload.items]
    edges = [ModelDeploymentEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ModelDeploymentConnection(
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
async def deployment(id: ID, info: Info[StrawberryGQLContext]) -> ModelDeployment | None:
    """Get a specific deployment by ID."""
    _, deployment_id = resolve_global_id(id)
    node = await info.context.adapters.deployment.get(UUID(deployment_id))
    return ModelDeployment.from_pydantic(node)


# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def create_model_deployment(
    input: CreateDeploymentInput, info: Info[StrawberryGQLContext]
) -> CreateDeploymentPayload:
    """Create a new model deployment."""
    user_data = current_user()
    if user_data is None:
        raise UserNotFound("User not found in context")
    payload = await info.context.adapters.deployment.create(input.to_pydantic(), user_data.user_id)
    return CreateDeploymentPayload(deployment=ModelDeployment.from_pydantic(payload.deployment))


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def update_model_deployment(
    input: UpdateDeploymentInput, info: Info[StrawberryGQLContext]
) -> UpdateDeploymentPayload:
    """Update an existing model deployment."""
    payload = await info.context.adapters.deployment.update(input.to_pydantic(), UUID(input.id))
    return UpdateDeploymentPayload(deployment=ModelDeployment.from_pydantic(payload.deployment))


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def delete_model_deployment(
    input: DeleteDeploymentInput, info: Info[StrawberryGQLContext]
) -> DeleteDeploymentPayload:
    """Delete a model deployment."""
    await info.context.adapters.deployment.delete(input.to_pydantic())
    return DeleteDeploymentPayload(id=input.id)


@strawberry.mutation(  # type: ignore[misc]
    description="Added in 25.16.0. Force syncs up-to-date replica information. In normal situations this will be automatically handled by Backend.AI schedulers"
)
async def sync_replicas(
    input: SyncReplicaInput, info: Info[StrawberryGQLContext]
) -> SyncReplicaPayload:
    payload = await info.context.adapters.deployment.sync_replicas(input.to_pydantic())
    return SyncReplicaPayload(success=payload.success)


# Subscription resolvers


@strawberry.subscription(description="Added in 25.16.0. Subscribe to deployment status changes")  # type: ignore[misc]
async def deployment_status_changed(
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    # TODO: Implement actual subscription logic using pub/sub system
    raise NotImplementedError("Subscription not implemented")
    yield  # type: ignore[unreachable]  # Makes this an async generator
