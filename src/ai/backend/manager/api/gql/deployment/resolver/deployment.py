"""Deployment resolver functions."""

from __future__ import annotations

from typing import AsyncGenerator, Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.deployment.fetcher.deployment import fetch_deployments
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
    SyncReplicaInput,
    SyncReplicaPayload,
    UpdateDeploymentInput,
    UpdateDeploymentPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import SyncReplicaAction
from ai.backend.manager.services.deployment.actions.update_deployment import UpdateDeploymentAction

# Query resolvers


@strawberry.field(description="Added in 25.16.0")
async def deployments(
    info: Info[StrawberryGQLContext],
    filter: Optional[DeploymentFilter] = None,
    order_by: Optional[list[DeploymentOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelDeploymentConnection:
    """List deployments with optional filtering and pagination."""
    return await fetch_deployments(
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
async def deployment(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ModelDeployment]:
    """Get a specific deployment by ID."""
    _, deployment_id = resolve_global_id(id)
    processor = info.context.processors.deployment
    result = await processor.get_deployment_by_id.wait_for_complete(
        GetDeploymentByIdAction(deployment_id=UUID(deployment_id))
    )
    return ModelDeployment.from_dataclass(result.data)


# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")
async def create_model_deployment(
    input: CreateDeploymentInput, info: Info[StrawberryGQLContext]
) -> CreateDeploymentPayload:
    """Create a new model deployment."""
    processor = info.context.processors.deployment
    result = await processor.create_deployment.wait_for_complete(
        CreateDeploymentAction(creator=input.to_creator())
    )

    return CreateDeploymentPayload(deployment=ModelDeployment.from_dataclass(result.data))


@strawberry.mutation(description="Added in 25.16.0")
async def update_model_deployment(
    input: UpdateDeploymentInput, info: Info[StrawberryGQLContext]
) -> UpdateDeploymentPayload:
    """Update an existing model deployment."""
    _, deployment_id = resolve_global_id(input.id)
    processor = info.context.processors.deployment
    action_result = await processor.update_deployment.wait_for_complete(
        UpdateDeploymentAction(updater=input.to_updater(UUID(deployment_id)))
    )
    return UpdateDeploymentPayload(deployment=ModelDeployment.from_dataclass(action_result.data))


@strawberry.mutation(description="Added in 25.16.0")
async def delete_model_deployment(
    input: DeleteDeploymentInput, info: Info[StrawberryGQLContext]
) -> DeleteDeploymentPayload:
    """Delete a model deployment."""
    _, deployment_id = resolve_global_id(input.id)
    deployment_processor = info.context.processors.deployment
    _ = await deployment_processor.destroy_deployment.wait_for_complete(
        DestroyDeploymentAction(endpoint_id=UUID(deployment_id))
    )
    return DeleteDeploymentPayload(id=input.id)


@strawberry.mutation(
    description="Added in 25.16.0. Force syncs up-to-date replica information. In normal situations this will be automatically handled by Backend.AI schedulers"
)
async def sync_replicas(
    input: SyncReplicaInput, info: Info[StrawberryGQLContext]
) -> SyncReplicaPayload:
    _, deployment_id = resolve_global_id(input.model_deployment_id)
    deployment_processor = info.context.processors.deployment
    await deployment_processor.sync_replicas.wait_for_complete(
        SyncReplicaAction(deployment_id=UUID(deployment_id))
    )
    return SyncReplicaPayload(success=True)


# Subscription resolvers


@strawberry.subscription(description="Added in 25.16.0. Subscribe to deployment status changes")
async def deployment_status_changed(
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    # TODO: Implement actual subscription logic using pub/sub system
    if False:  # Placeholder to satisfy type checker
        yield DeploymentStatusChangedPayload(deployment=ModelDeployment())
